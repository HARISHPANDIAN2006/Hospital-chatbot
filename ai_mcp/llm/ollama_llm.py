import requests


class OllamaLLM:
    def __init__(self, model="qwen2.5:3b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, context: str, question: str) -> str:
        payload = {
            "model": self.model,
            "prompt": f"""
You are an assistant that answers strictly using the context below.

CONTEXT:
{context}

QUESTION:
{question}

If the answer is not present in the context, say:
"I do not have that information."
""",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 1024,
                "num_predict": 128
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300   # 5 minutes hard limit
            )
            response.raise_for_status()
            return response.json()["response"].strip()

        except requests.exceptions.ReadTimeout:
            return (
                "The local language model is taking too long to respond. "
                "Please try again or ask a shorter question."
            )
