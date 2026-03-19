"""
Gemini LLM for the RAG chatbot. Uses Google Gemini API (e.g. Gemini 2.5 Flash).
API key must be set via GEMINI_API_KEY environment variable or .env.
"""

import os

try:
    from google import genai as google_genai  # New SDK: google-genai
except Exception:
    google_genai = None

try:
    import google.generativeai as google_generativeai  # Legacy SDK: google-generativeai
except Exception:
    google_generativeai = None


class GeminiLLM:
    """
    LLM that calls Google Gemini API for RAG answers.
    Uses the same generate(context, question) interface as OllamaLLM.
    """

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY or GOOGLE_API_KEY is not set. Set it in .env or environment variables."
            )
        # e.g. gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.sdk = None
        self.client = None

        if google_genai is not None:
            self.client = google_genai.Client(api_key=self.api_key)
            self.sdk = "google-genai"
        elif google_generativeai is not None:
            google_generativeai.configure(api_key=self.api_key)
            self.client = google_generativeai.GenerativeModel(self.model_name)
            self.sdk = "google-generativeai"
        else:
            raise RuntimeError(
                "Gemini SDK not installed. Install one of: 'google-genai' (recommended) or 'google-generativeai'."
            )

    def generate(self, context: str, question: str) -> str:
        prompt = f"""You are a helpful hospital assistant. Answer the question using ONLY the context below.

CONTEXT:
{context}

QUESTION:
{question}

Rules:
- If the answer is not in the context, say: "I do not have that information."
- Be concise and relevant. Do not invent information."""

        try:
            if self.sdk == "google-genai":
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "temperature": 0.1,
                        "max_output_tokens": 512,
                    },
                )
                text = (getattr(response, "text", "") or "").strip()
                if not text and getattr(response, "candidates", None):
                    parts = []
                    for candidate in response.candidates:
                        content = getattr(candidate, "content", None)
                        if not content:
                            continue
                        for part in getattr(content, "parts", []) or []:
                            if getattr(part, "text", ""):
                                parts.append(part.text)
                    text = "\n".join(parts).strip()
            else:
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 512,
                    },
                )
                text = (getattr(response, "text", "") or "").strip()

            if not text:
                return "I do not have that information."
            return text
        except Exception as e:
            return (
                f"Sorry, the AI service could not respond: {getattr(e, 'message', str(e))}. "
                "Please try again."
            )
