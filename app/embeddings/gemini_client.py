from typing import List

from google import genai

from app.core.config import settings


class GeminiEmbeddingClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_embed_model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
            )
            vectors.append(result.embeddings[0].values)
        return vectors

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]
