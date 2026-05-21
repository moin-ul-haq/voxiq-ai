"""
OAuth REST API helpers.

Reads provider credentials from SOCIALACCOUNT_PROVIDERS in settings.py
(configured by django-allauth) and provides functions to:
  - Build consent screen URLs
  - Exchange authorization codes for access tokens
  - Fetch & normalize user info from each provider
  - Find or create Django users by email
"""

import requests
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


# ──────────────────────────────────────────────────────
# Provider URL Configuration
# ──────────────────────────────────────────────────────

# Maps our clean provider names to allauth's internal provider keys
ALLAUTH_PROVIDER_KEYS = {
    "google": "google",
    "github": "github",
    "linkedin": "linkedin_oauth2",
}

# OAuth endpoints for each provider
PROVIDER_URLS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_info_url": "https://api.github.com/user",
    },
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "user_info_url": "https://api.linkedin.com/v2/userinfo",
    },
}

SUPPORTED_PROVIDERS = list(PROVIDER_URLS.keys())


# ──────────────────────────────────────────────────────
# Credential helpers (reads from allauth settings)
# ──────────────────────────────────────────────────────

def _get_allauth_app(provider: str) -> dict:
    """
    Read client_id and secret from SOCIALACCOUNT_PROVIDERS in settings.py.
    This is the same config allauth uses, so credentials stay in one place.
    """
    allauth_key = ALLAUTH_PROVIDER_KEYS.get(provider, provider)
    provider_conf = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(allauth_key, {})
    return provider_conf.get("APP", {})


def _get_scopes(provider: str) -> str:
    """Read scopes from SOCIALACCOUNT_PROVIDERS, with sensible defaults."""
    allauth_key = ALLAUTH_PROVIDER_KEYS.get(provider, provider)
    provider_conf = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(allauth_key, {})
    scopes = provider_conf.get("SCOPE", [])
    if scopes:
        return " ".join(scopes)
    # Defaults
    defaults = {
        "google": "openid email profile",
        "github": "read:user user:email",
        "linkedin": "openid profile email",
    }
    return defaults.get(provider, "")


def validate_provider(provider: str):
    """Raise ValueError if the provider is not supported."""
    if provider not in PROVIDER_URLS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Unsupported provider '{provider}'. Supported: {supported}")


# ──────────────────────────────────────────────────────
# Step 1: Build the consent screen URL
# ──────────────────────────────────────────────────────

def build_auth_url(provider: str, redirect_uri: str) -> str:
    """
    Build the full OAuth authorization URL for the given provider.
    The frontend redirects the user to this URL (popup or full redirect).
    """
    validate_provider(provider)
    app = _get_allauth_app(provider)
    urls = PROVIDER_URLS[provider]

    params = {
        "client_id": app.get("client_id", ""),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _get_scopes(provider),
    }

    # Google needs access_type for refresh tokens
    if provider == "google":
        params["access_type"] = "online"

    return f"{urls['auth_url']}?{urlencode(params)}"


# ──────────────────────────────────────────────────────
# Step 2: Exchange authorization code for access token
# ──────────────────────────────────────────────────────

def exchange_code_for_token(provider: str, code: str, redirect_uri: str) -> str:
    """
    Exchange the authorization code for an access token.
    Returns the access_token string.
    """
    validate_provider(provider)
    app = _get_allauth_app(provider)
    urls = PROVIDER_URLS[provider]

    payload = {
        "client_id": app.get("client_id", ""),
        "client_secret": app.get("secret", ""),
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    response = requests.post(
        urls["token_url"],
        data=payload,
        headers={"Accept": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    # GitHub returns errors in 200 responses with an "error" key
    if "error" in data:
        raise ValueError(
            f"OAuth token error: {data.get('error_description', data['error'])}"
        )

    return data["access_token"]


# ──────────────────────────────────────────────────────
# Step 3: Fetch user info from the provider
# ──────────────────────────────────────────────────────

def get_user_info(provider: str, access_token: str) -> dict:
    """
    Fetch user info and return a normalized dict:
        { "email": "...", "first_name": "...", "last_name": "..." }
    """
    validate_provider(provider)
    urls = PROVIDER_URLS[provider]

    response = requests.get(
        urls["user_info_url"],
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    # Each provider returns data in a different shape — normalize it
    return USER_INFO_PARSERS[provider](data, access_token)


def _parse_google(data: dict, access_token: str) -> dict:
    return {
        "email": data.get("email", ""),
        "first_name": data.get("given_name", ""),
        "last_name": data.get("family_name", ""),
    }


def _parse_github(data: dict, access_token: str) -> dict:
    email = data.get("email")

    # GitHub users can have private emails — fetch from /user/emails
    if not email:
        email = _fetch_github_primary_email(access_token)

    full_name = data.get("name", "") or ""
    parts = full_name.split(" ", 1)

    return {
        "email": email or "",
        "first_name": parts[0] if parts else "",
        "last_name": parts[1] if len(parts) > 1 else "",
    }


def _fetch_github_primary_email(access_token: str) -> str:
    """Fetch the primary verified email from GitHub's /user/emails endpoint."""
    response = requests.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    response.raise_for_status()

    for entry in response.json():
        if entry.get("primary") and entry.get("verified"):
            return entry["email"]
    return ""


def _parse_linkedin(data: dict, access_token: str) -> dict:
    return {
        "email": data.get("email", ""),
        "first_name": data.get("given_name", ""),
        "last_name": data.get("family_name", ""),
    }


USER_INFO_PARSERS = {
    "google": _parse_google,
    "github": _parse_github,
    "linkedin": _parse_linkedin,
}


# ──────────────────────────────────────────────────────
# Step 4: Find or create the Django user
# ──────────────────────────────────────────────────────

def get_or_create_oauth_user(email: str, first_name: str, last_name: str):
    """
    Look up a user by email:
    - Found → return existing user (same account, no duplicate)
    - Not found → create a new user with an unusable password (OAuth-only)

    This ensures email/password users who later use OAuth with the same
    email are logged into their EXISTING account.
    """
    if not email:
        raise ValueError("OAuth provider did not return an email address.")

    user = User.objects.filter(email=email).first()
    if user:
        return user

    # New OAuth-only user
    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])

    return user
