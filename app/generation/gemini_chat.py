from google import genai

from app.core.config import settings


class GeminiChatClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_chat_model

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        text = response.text
        if not text:
            raise ValueError("No response returned from Gemini.")
        return text.strip()
