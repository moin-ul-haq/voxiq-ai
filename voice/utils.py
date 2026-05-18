import requests
from django.conf import settings


VAPI_API_URL = "https://api.vapi.ai"


def build_vapi_system_prompt(interview, user) -> str:
    """
    Build dynamic system prompt for VAPI mock interview assistant.
    More structured than chatbot — focuses on conducting the interview.
    """
    resume_section = ""
    if user.resume_text:
        resume_section = f"""
## Candidate Resume
{user.resume_text}
"""

    return f"""You are Voxiq, a professional AI interviewer conducting a mock job interview.

## Your Role
- Conduct a realistic, professional mock interview for the position below
- Ask one question at a time and wait for the candidate's response
- Ask relevant follow-up questions based on their answers
- Cover technical skills, behavioral questions, and situational scenarios
- At the end, give brief honest feedback on their performance

## Target Position
**Job Title:** {interview.job_title}
**Job Description:**
{interview.job_description}
{resume_section}
## Interview Guidelines
- Start by greeting the candidate and introducing yourself
- Ask 6-8 questions total — mix of technical and behavioral
- Keep your questions concise and clear
- Do not give answers or hints — let the candidate respond fully
- Be professional but conversational in tone
- End the interview politely and tell them feedback will be shared

## Important
- This is a VOICE interview — keep responses short and natural
- Do not use bullet points or markdown in your responses
- Speak naturally as you would in a real interview
- Keep each response under 3 sentences maximum
- Never give long explanations or lectures
- If you need to elaborate, break it into follow-up questions instead
- Acknowledge the candidate's answer briefly, then move on
"""


def create_vapi_assistant(interview, user) -> dict:
    """
    Create a dynamic VAPI assistant for this specific interview.
    Returns VAPI assistant object with id.
    """
    system_prompt = build_vapi_system_prompt(interview, user)

    headers = {
        "Authorization": f"Bearer {settings.VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "name": f"Voxiq — {interview.job_title[:30]}",
        "model": {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ],
            "temperature": 0.7,
        },
        "voice": {
    "provider": "11labs",
    "voiceId": "sarah",
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en-US",
        },
        "firstMessage": f"Hello! I'm your Voxiq interviewer today. We'll be doing a mock interview for the {interview.job_title} position. Are you ready to begin?",
        "endCallMessage": "Thank you for your time. That concludes our mock interview. You'll be able to review the transcript shortly. Good luck!",
        "endCallPhrases": ["goodbye", "thank you bye", "end interview", "stop interview"],
    }

    response = requests.post(
        f"{VAPI_API_URL}/assistant",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if not response.ok:
        print(f"VAPI Error: {response.status_code} - {response.text}")
    response.raise_for_status()
    return response.json()


def delete_vapi_assistant(assistant_id: str):
    """
    Delete VAPI assistant after call ends to keep account clean.
    Called from webhook after session completes.
    """
    headers = {
        "Authorization": f"Bearer {settings.VAPI_API_KEY}",
    }

    try:
        requests.delete(
            f"{VAPI_API_URL}/assistant/{assistant_id}",
            headers=headers,
            timeout=10,
        )
    except Exception:
        pass  # Non-critical — log but don't fail