# Voxiq Frontend Integration Guide

This document outlines the recent backend updates and provides the exact API endpoints and JSON structures you need to integrate the frontend.

## 1. OAuth Flow (Frontend Managed with Redirect)

This is a frontend-driven OAuth flow. The frontend acts as the callback handler, retrieves the `code` from Google, and securely sends it to the Django backend for token exchange.

### Step 1: Get the Auth URL
Call this endpoint to get the provider's consent screen URL.

**Request (No Auth Required):**
`GET /api/auth/oauth/google/auth-url/?redirect_uri=http://localhost:5173/auth/callback`

*(If you omit `redirect_uri`, it defaults to the `FRONTEND_URL` in Django settings + `/auth/callback`)*

**Response (200 OK):**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=http://localhost:5173/auth/callback&...",
  "redirect_uri": "http://localhost:5173/auth/callback"
}
```

**Frontend Action:** Redirect the user's browser window to the `auth_url`.

---

### Step 2: Handle the Callback & Exchange Code
After the user approves on the Google consent screen, Google will redirect them back to your frontend URL:
`http://localhost:5173/auth/callback?code=4/0A...`

**Frontend Action:**
1. Extract the `code` from the URL search parameters.
2. Make a `POST` request to the backend to exchange this code for JWT tokens.

**Request to Backend (No Auth Required):**
`POST /api/auth/oauth/google/login/`

**Request Body:**
```json
{
  "code": "4/0A...",
  "redirect_uri": "http://localhost:5173/auth/callback" 
}
```
*(Note: The `redirect_uri` you send here MUST exactly match the one used in Step 1).*

**Response (200 OK):**
The backend will validate the code, create the user if needed, and issue your JWTs.
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

> **Registered Redirect URIs in Google/GitHub/LinkedIn Console:**
> These are the exact URLs you must whitelist in each provider's developer console. They should be your FRONTEND URLs, for example:
> - **Google:** `http://localhost:5173/auth/callback`
> - **GitHub:** `http://localhost:5173/auth/callback`
> - **LinkedIn:** `http://localhost:5173/auth/callback`



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
