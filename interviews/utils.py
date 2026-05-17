from groq import Groq
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def build_system_prompt(interview, user) -> str:
    """
    Build dynamic system prompt for interview prep chatbot.
    Injects job title, job description, and user resume into context.
    """
    resume_section = ""
    if user.resume_text:
        resume_section = f"""
## Candidate Resume
{user.resume_text}
"""

    return f"""You are Voxiq, an expert AI interview coach helping candidates prepare for job interviews.

## Your Role
- Help the candidate prepare thoroughly for their upcoming interview
- Explain important concepts clearly with examples
- Suggest likely interview questions based on the job description
- Give actionable tips and feedback
- Be encouraging but honest about weak areas

## Target Job
**Title:** {interview.job_title}
**Description:**
{interview.job_description}
{resume_section}
## Guidelines
- Focus only on topics relevant to this specific job
- If the candidate asks something unrelated to interview prep, politely redirect
- When suggesting questions, also provide strong example answers
- Keep responses clear, structured, and concise
"""


def get_groq_response(interview, user, chat_history: list) -> str:
    """
    Send conversation history to Groq and return assistant response.

    chat_history: list of dicts [{"role": "user/assistant", "content": "..."}]
    """
    system_prompt = build_system_prompt(interview, user)

    messages = [{"role": "system", "content": system_prompt}] + chat_history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )

    return response.choices[0].message.content