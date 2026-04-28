from app.agent.graph import SparkAgent
from app.schemas.documents import Chunk, ChunkMetadata


class FakeChatClient:
    def generate(self, prompt: str) -> str:
        assert "Retrieved Context:" in prompt
        return "RAG answer from fake docs. Sources Used: [1]"


class FakePipeline:
    def __init__(self, chunks):
        self.chunks = chunks
        self.chat_client = FakeChatClient()

    def retrieve(self, question: str, limit: int = 4):
        return self.chunks[:limit]


def make_chunk(chunk_id: str = "chunk-1") -> Chunk:
    return Chunk(
        metadata=ChunkMetadata(
            chunk_id=chunk_id,
            doc_id="rag-basics",
            title="RAG Basics",
            source="data/raw/ai/rag_basics.md",
            space="AI",
            section="Grounding",
            chunk_index=0,
            tags=["rag"],
        ),
        content="RAG grounds answers in retrieved context.",
    )


def test_agent_routes_arithmetic_to_calculator_tool() -> None:
    agent = SparkAgent(pipeline=FakePipeline(chunks=[]))

    state = agent.invoke("What is 12 * (3 + 2)?")

    assert state["route"] == "tool"
    assert state["tool_name"] == "calculator_tool"
    assert state["answer"] == "12 * (3 + 2) = 60"
    assert state["retrieved_chunks"] == []


def test_agent_routes_document_questions_to_rag() -> None:
    agent = SparkAgent(pipeline=FakePipeline(chunks=[make_chunk()]))

    state = agent.invoke("How does RAG reduce hallucination?")

    assert state["route"] == "rag"
    assert state["tool_name"] == "doc_lookup_tool"
    assert state["answer"] == "RAG answer from fake docs. Sources Used: [1]"
    assert len(state["retrieved_chunks"]) == 1
    assert state["retrieved_chunks"][0].metadata.chunk_id == "chunk-1"


def test_agent_falls_back_when_retrieval_finds_no_chunks() -> None:
    agent = SparkAgent(pipeline=FakePipeline(chunks=[]))

    state = agent.invoke("Tell me about the deployment process.")

    assert state["route"] == "rag"
    assert state["tool_name"] == "doc_lookup_tool"
    assert state["answer"].startswith("I could not find enough reliable documentation")
    assert state["retrieved_chunks"] == []
