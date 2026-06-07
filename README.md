# VoxIQ - AI Mock Interview Platform

**Live Application:** [https://voxiq-ai.vercel.app](https://voxiq-ai.vercel.app)

Welcome to the VoxIQ backend repository! This document outlines how to set up the Django backend environment locally and provides an overview of the REST API endpoints consumed by the React (Vite) frontend.

## Prerequisites

- Python 3.10+
- pip (Python package installer)

## Local Setup

1. **Navigate to the project directory:**
   ```bash
   cd d:\python\django\voxiq
   ```

2. **Create and activate a virtual environment:**
   - **Windows:**
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory (where `manage.py` is located) with the following required API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key
   VAPI_API_KEY=your_vapi_api_key
   VAPI_WEBHOOK_SECRET=your_vapi_webhook_secret
   ```

5. **Run Database Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The backend will now be available at `http://127.0.0.1:8000/`.

## Authentication

This project uses **JSON Web Tokens (JWT)** for authentication. 
For protected endpoints, include the access token in the `Authorization` header of your HTTP requests:

```http
Authorization: Bearer <your_access_token>
```

## API Endpoints

Base URL: `http://127.0.0.1:8000`

### Authentication (`/api/auth/`)
- `POST /api/auth/register/` - Register a new user.
- `POST /api/auth/login/` - Login and receive JWT access and refresh tokens.
- `POST /api/auth/logout/` - Logout (blacklists the token).
- `POST /api/auth/token/refresh/` - Refresh the JWT access token using the refresh token.
- `GET /api/auth/profile/` - Get the current authenticated user's profile data.
- `POST /api/auth/profile/resume/` - Upload the user's resume (`multipart/form-data`).
- `POST /api/auth/onboarding/complete/` - Mark the user's onboarding process as complete.

### Interviews (`/api/interviews/`)
- `GET /api/interviews/` - List all interviews for the authenticated user.
- `POST /api/interviews/` - Create a new interview.
- `GET /api/interviews/<id>/` - Retrieve details of a specific interview.
- `POST /api/interviews/<id>/chat/` - Text chat endpoint for an interview (powered by Groq).

### Voice & VAPI (`/api/voice/`)
- `POST /api/voice/interviews/<id>/session/start/` - Start a voice session for an interview.
- `GET /api/voice/interviews/<id>/sessions/` - List all voice sessions for an interview.
- `GET /api/voice/sessions/<id>/` - Retrieve details of a specific voice session.
- `POST /api/voice/webhook/vapi/` - VAPI webhook endpoint (Primarily for VAPI callbacks).

## Important Notes for Frontend
- **File Uploads:** When hitting `/api/auth/profile/resume/`, ensure you use `FormData` in JavaScript so the `multipart/form-data` encoding is correctly applied for file uploads.
- **Handling Tokens:** Store your JWT tokens securely (e.g., HttpOnly cookies or secure local storage) and ensure you handle `401 Unauthorized` errors by attempting to refresh the token via `/api/auth/token/refresh/`.
