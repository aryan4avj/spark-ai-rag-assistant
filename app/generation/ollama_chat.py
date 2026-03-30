import requests

from app.core.config import settings


class OllamaChatClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_chat_model

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("response")
        if not text:
            raise ValueError("No response returned from Ollama.")
        return text.strip()
