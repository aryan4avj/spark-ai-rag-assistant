import ast
import operator
import re
import time
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.generation.prompts import build_rag_prompt
from app.retrieval.rag_pipeline import RAGPipeline
from app.schemas.documents import Chunk


class AgentState(TypedDict, total=False):
    question: str
    top_k: int
    route: str
    retrieved_chunks: List[Chunk]
    tool_name: Optional[str]
    tool_result: Optional[str]
    answer: str
    timing_ms: Dict[str, float]


class Calculator:
    """Small arithmetic tool used by the agent's tool path."""

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def run(self, expression: str) -> str:
        cleaned_expression = self._extract_expression(expression)
        if not cleaned_expression:
            return "I could not find a calculation to run."

        try:
            parsed_expression = ast.parse(cleaned_expression, mode="eval")
            result = self._evaluate(parsed_expression.body)
        except (SyntaxError, ValueError, ZeroDivisionError) as error:
            return f"I could not calculate that: {error}"

        return f"{cleaned_expression} = {result}"

    def _extract_expression(self, text: str) -> str:
        allowed_characters = re.findall(r"[0-9+\-*/().\s]+", text)
        return "".join(allowed_characters).strip()

    def _evaluate(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in self.allowed_operators:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return self.allowed_operators[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in self.allowed_operators:
            operand = self._evaluate(node.operand)
            return self.allowed_operators[type(node.op)](operand)

        raise ValueError("only basic arithmetic is supported")


class DocLookupTool:
    """Thin wrapper around Qdrant retrieval so the graph has a named doc tool."""

    name = "doc_lookup_tool"

    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    def run(self, question: str, limit: int) -> List[Chunk]:
        return self.pipeline.retrieve(question=question, limit=limit)


class SparkAgent:
    def __init__(self, pipeline: Optional[RAGPipeline] = None) -> None:
        self.pipeline = pipeline or RAGPipeline()
        self.calculator = Calculator()
        self.doc_lookup_tool = DocLookupTool(self.pipeline)
        self.graph = self._build_graph()

    def invoke(self, question: str, top_k: int = 4) -> AgentState:
        return self.graph.invoke(
            {
                "question": question,
                "top_k": top_k,
                "retrieved_chunks": [],
                "tool_name": None,
                "tool_result": None,
                "timing_ms": {},
            }
        )

    def _build_graph(self):
        graph = StateGraph(AgentState)

        # Each node receives the shared state and returns only the fields it changes.
        graph.add_node("route_question", self.route_question)
        graph.add_node("retrieve_documents", self.retrieve_documents)
        graph.add_node("call_tool", self.call_tool)
        graph.add_node("generate_answer", self.generate_answer)
        graph.add_node("return_fallback", self.return_fallback)

        graph.set_entry_point("route_question")
        graph.add_conditional_edges(
            "route_question",
            self._route_after_question,
            {
                "rag": "retrieve_documents",
                "tool": "call_tool",
                "fallback": "return_fallback",
            },
        )
        graph.add_conditional_edges(
            "retrieve_documents",
            self._route_after_retrieval,
            {
                "generate": "generate_answer",
                "fallback": "return_fallback",
            },
        )
        graph.add_edge("call_tool", END)
        graph.add_edge("generate_answer", END)
        graph.add_edge("return_fallback", END)

        return graph.compile()

    def route_question(self, state: AgentState) -> Dict[str, Any]:
        started_at = time.perf_counter()
        question = state["question"].strip()

        if self._looks_like_arithmetic(question):
            route = "tool"
        elif not question:
            route = "fallback"
        else:
            route = "rag"

        return {
            "route": route,
            "timing_ms": self._with_timing(state, "route_question", started_at),
        }

    def retrieve_documents(self, state: AgentState) -> Dict[str, Any]:
        started_at = time.perf_counter()
        chunks = self.doc_lookup_tool.run(
            question=state["question"],
            limit=state.get("top_k", 4),
        )
        return {
            "tool_name": self.doc_lookup_tool.name,
            "retrieved_chunks": chunks,
            "timing_ms": self._with_timing(state, "retrieve_documents", started_at),
        }

    def call_tool(self, state: AgentState) -> Dict[str, Any]:
        started_at = time.perf_counter()
        tool_result = self.calculator.run(state["question"])
        return {
            "tool_name": "calculator_tool",
            "tool_result": tool_result,
            "answer": tool_result,
            "timing_ms": self._with_timing(state, "call_tool", started_at),
        }

    def generate_answer(self, state: AgentState) -> Dict[str, Any]:
        started_at = time.perf_counter()
        prompt = build_rag_prompt(
            question=state["question"],
            chunks=state.get("retrieved_chunks", []),
        )
        answer = self.pipeline.chat_client.generate(prompt)
        return {
            "answer": answer,
            "timing_ms": self._with_timing(state, "generate_answer", started_at),
        }

    def return_fallback(self, state: AgentState) -> Dict[str, Any]:
        started_at = time.perf_counter()
        fallback = (
            "I could not find enough reliable documentation context to answer that. "
            "Try asking about the indexed product, engineering, platform, or AI docs."
        )
        return {
            "route": state.get("route", "fallback"),
            "answer": fallback,
            "timing_ms": self._with_timing(state, "return_fallback", started_at),
        }

    def _route_after_question(self, state: AgentState) -> str:
        return state["route"]

    def _route_after_retrieval(self, state: AgentState) -> str:
        if state.get("retrieved_chunks"):
            return "generate"
        return "fallback"

    def _looks_like_arithmetic(self, question: str) -> bool:
        arithmetic_words = ("calculate", "calculator", "what is", "sum", "multiply")
        has_operator = bool(re.search(r"\d\s*[+\-*/]\s*\d", question))
        has_numbers = len(re.findall(r"\d+", question)) >= 2
        return has_operator or (
            has_numbers and any(word in question.lower() for word in arithmetic_words)
        )

    def _with_timing(
        self,
        state: AgentState,
        node_name: str,
        started_at: float,
    ) -> Dict[str, float]:
        timings = dict(state.get("timing_ms", {}))
        timings[node_name] = round((time.perf_counter() - started_at) * 1000, 2)
        return timings
