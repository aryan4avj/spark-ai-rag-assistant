from fastapi import APIRouter

from app.agent.graph import SparkAgent
from app.api.query import to_chunk_response
from app.schemas.query import AgentQueryResponse, QueryRequest

router = APIRouter(prefix="/agent", tags=["agent"])

agent = SparkAgent()


@router.post("/query", response_model=AgentQueryResponse)
def agent_query(request: QueryRequest) -> AgentQueryResponse:
    state = agent.invoke(question=request.question, top_k=request.top_k)

    return AgentQueryResponse(
        question=request.question,
        route=state["route"],
        answer=state["answer"],
        sources=[
            to_chunk_response(chunk, source_number=i)
            for i, chunk in enumerate(state.get("retrieved_chunks", []), start=1)
        ],
        tool_name=state.get("tool_name"),
        tool_result=state.get("tool_result"),
        timing_ms=state.get("timing_ms", {}),
    )
