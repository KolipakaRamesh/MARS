"""
MARS — Shared Agent State (the blackboard).

All agents read from and write to this TypedDict.
Agents NEVER call each other directly — all communication goes through state.

LangGraph uses Annotated[List, operator.add] to safely accumulate list fields
across concurrent or sequential node executions.
"""
from typing import TypedDict, Annotated, List, Optional
import operator


class AgentState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    query: str
    session_id: str

    # ── Planner output ───────────────────────────────────────────────────────
    subtasks: List[str]
    current_subtask_index: int

    # ── Research output (append-only accumulator) ────────────────────────────
    raw_research: Annotated[List[str], operator.add]

    # ── Memory context injected before research ──────────────────────────────
    memory_context: str

    # ── Analyst output ───────────────────────────────────────────────────────
    synthesized_answer: str

    # ── Reviewer output ──────────────────────────────────────────────────────
    quality_score: float          # 0.0 – 1.0
    verdict: str                  # "PASS" | "RETRY" | "ESCALATE"
    feedback: str                 # reviewer's improvement notes

    # ── Control flow ─────────────────────────────────────────────────────────
    iteration_count: int
    max_iterations: int
    error: Optional[str]

    # ── LLM usage (append-only, one entry per LLM call) ────────────────────────
    # Each entry: {agent, model, prompt_tokens, completion_tokens, total_tokens, latency_ms}
    llm_usage: Annotated[List[dict], operator.add]

    # ── Audit trail (append-only) ────────────────────────────────────────────
    agent_trace: Annotated[List[dict], operator.add]


def initial_state(query: str, session_id: str = "default") -> AgentState:
    """Factory — returns a clean initial state for a new query."""
    return AgentState(
        query=query,
        session_id=session_id,
        subtasks=[],
        current_subtask_index=0,
        raw_research=[],
        memory_context="",
        synthesized_answer="",
        quality_score=0.0,
        verdict="",
        feedback="",
        iteration_count=0,
        max_iterations=3,
        error=None,
        llm_usage=[],
        agent_trace=[],
    )
