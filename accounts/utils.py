import pypdf
import io


def extract_text_from_resume(resume_file) -> str:
    """
    Extract plain text from an uploaded PDF resume.
    Called after resume upload — result saved to user.resume_text
    for use in AI system prompts.
    """
    try:
        # Read file into memory buffer
        file_content = resume_file.read()
        pdf_buffer = io.BytesIO(file_content)

        reader = pypdf.PdfReader(pdf_buffer)
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        extracted = "\n".join(text_parts).strip()
        return extracted if extracted else ""

    except Exception as e:
        # Fail silently — resume still uploads, AI just won't have resume context
        print(f"Resume text extraction failed: {e}")
        return ""