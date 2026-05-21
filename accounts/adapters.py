"""
Custom allauth adapters.

- SocialAccountAdapter: Sets username = email (matching existing convention)
  and auto-connects OAuth logins to existing users with the same email.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        """
        Called when a new user is being created via social login.
        Sets username = email to match the existing registration convention.
        """
        user = super().populate_user(request, sociallogin, data)
        email = data.get("email", "")
        if email:
            user.username = email
        return user
