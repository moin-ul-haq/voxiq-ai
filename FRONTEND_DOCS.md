# Voxiq Frontend Integration Guide

This document outlines the recent backend updates and provides the exact API endpoints and JSON structures you need to integrate the frontend.

## 1. OAuth Flow (100% Backend Managed — Single Step)

This is a fully backend-managed OAuth flow. The frontend **never** needs to handle the code exchange — the backend does it automatically. There are only **two things the frontend needs to do**:

### Step 1: Get the Auth URL
Call this endpoint to get the provider's consent screen URL. The backend automatically builds the correct `redirect_uri` pointing back to itself.

**Request (No Auth Required):**
`GET /api/auth/oauth/google/auth-url/`

**Response (200 OK):**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=http://localhost:8000/api/auth/oauth/google/callback/&..."
}
```

**Frontend Action:** Redirect the user's browser window to the `auth_url`. *(Either a full page redirect, or open in a popup/new tab.)*

---

### Step 2: Receive the JWT Tokens (Backend handles everything in between)

After the user approves on the consent screen, Google redirects them to `http://localhost:8000/api/auth/oauth/google/callback/`. The backend then automatically:
1. Extracts the authorization code from the URL.
2. Exchanges it for a Google access token (server-to-server, secure).
3. Fetches the user's email, name etc. from Google.
4. Finds or creates the user in the database.
5. Issues our own JWT tokens and returns them directly.

The final **JSON response** lands on the browser at the callback URL:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "onboarding_complete": false
  }
}
```

**Frontend Action:** You can handle this in two ways:
- **Option A (Popup):** Open the auth URL in a popup window. Listen for the popup page URL to change to the callback URL, extract the JSON response from the popup, and close it.
- **Option B (Redirect + Parse):** Redirect the full page to the auth URL. When the browser lands on the callback URL showing the JSON, your frontend route at that URL can parse the JSON from the response body.

> **Registered Redirect URIs in Google/GitHub/LinkedIn Console:**
> These are the exact URLs you must whitelist in each provider's developer console:
> - **Google:** `http://localhost:8000/api/auth/oauth/google/callback/`
> - **GitHub:** `http://localhost:8000/api/auth/oauth/github/callback/`
> - **LinkedIn:** `http://localhost:8000/api/auth/oauth/linkedin_oauth2/callback/`


## 2. Voice Interview AI Evaluations

When a user finishes speaking with the VAPI AI agent, the backend automatically intercepts the webhook, parses the transcript, and uses an LLM to generate a detailed evaluation scorecard.

### Get Past Sessions (with Evaluations)
To show a user their past mock interviews for a specific job:

**Request:** (Requires JWT Token)
`GET /api/voice/interviews/<interview_id>/sessions/`

**Response (200 OK):**
```json
[
  {
    "id": 15,
    "vapi_call_id": "call_abc123",
    "status": "completed",
    "transcript": "User: Hello... Assistant: Let's begin...",
    "duration_seconds": 340,
    "started_at": "2026-05-21T10:00:00Z",
    "ended_at": "2026-05-21T10:05:40Z",
    "evaluation": {
      "overall_score": 85,
      "metrics": {
        "technical_competence": 80,
        "communication_skills": 90,
        "problem_solving": 85
      },
      "strengths": [
        "Clear explanation of React hooks",
        "Good professional tone"
      ],
      "areas_for_improvement": [
        "Rambled slightly on the database question"
      ],
      "detailed_feedback": "Overall a strong interview, but try to structure behavioral answers using the STAR method..."
    }
  }
]
```
*(Note: You can also fetch a single session via `GET /api/voice/sessions/<session_id>/`)*

**Frontend Action:** Use the `evaluation` JSON object to render beautiful progress bars (out of 100) and bulleted feedback lists for the user.


## 3. Resume Uploads (Cloudflare R2)

Resumes are no longer stored on the server disk; they stream directly to an S3-compatible Cloudflare R2 bucket.

### Uploading a Resume
**Request:** (Requires JWT Token, `multipart/form-data`)
`POST /api/auth/profile/resume/`
*(Attach the PDF file to the form data under the key `resume`)*

**Response (200 OK):**
```json
{
  "message": "Resume uploaded successfully",
  "resume_url": "https://voxiq-resumes.r2.cloudflarestorage.com/media/resumes/user_1/cv.pdf"
}
```

### Retrieving User Data & Resume Link
To get the current user's profile and resume link at any time:

**Request:** (Requires JWT Token)
`GET /api/auth/profile/`

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "resume": "https://voxiq-resumes.r2.cloudflarestorage.com/media/resumes/user_1/cv.pdf",
  "onboarding_complete": true
}
```
**Frontend Action:** Use the `resume` URL to render a "Download My Resume" or "View PDF" button. Since the bucket is properly configured, the link will serve the file directly via Cloudflare's global CDN.
