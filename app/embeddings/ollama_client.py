from typing import List

import requests

from app.core.config import settings


class OllamaEmbeddingClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embed_model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={
                "model": self.model,
                "input": texts,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        embeddings = data.get("embeddings")
        if embeddings is None:
            raise ValueError("No embeddings returned from Ollama.")
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]
