from app.core.config import settings
from app.embeddings.gemini_client import GeminiEmbeddingClient
from app.embeddings.ollama_client import OllamaEmbeddingClient
from app.generation.gemini_chat import GeminiChatClient
from app.generation.ollama_chat import OllamaChatClient


def get_embedding_client():
    if settings.embed_provider == "gemini":
        return GeminiEmbeddingClient()
    return OllamaEmbeddingClient()


def get_chat_client():
    if settings.llm_provider == "gemini":
        return GeminiChatClient()
    return OllamaChatClient()
