"""
MARS — LangGraph Orchestration Graph.

Graph topology:
  planner → research (loop until all subtasks done) → analyst → reviewer
  reviewer → analyst (RETRY) | END (PASS | ESCALATE)

The graph is compiled once at startup and reused for all requests.
"""
import logging
from langgraph.graph import StateGraph, END
from backend.orchestration.state import AgentState
from backend.orchestration.router import route_after_research, route_after_review

logger = logging.getLogger(__name__)


def build_graph(planner, research, analyst, reviewer):
    """
    Wire up the StateGraph with all agents and conditional edges.
    Returns a compiled, executable graph.

    Args:
        planner:  PlannerAgent instance
        research: ResearchAgent instance
        analyst:  AnalystAgent instance
        reviewer: ReviewerAgent instance
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("planner",  planner.run)
    graph.add_node("research", research.run)
    graph.add_node("analyst",  analyst.run)
    graph.add_node("reviewer", reviewer.run)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("planner")

    # ── Static edges ──────────────────────────────────────────────────────────
    graph.add_edge("planner",  "research")
    graph.add_edge("analyst",  "reviewer")

    # ── Conditional edges ─────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "research",
        route_after_research,
        {
            "research": "research",   # loop: more subtasks remain
            "analyst":  "analyst",    # done: all subtasks complete
        },
    )

    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "analyst": "analyst",     # RETRY: re-synthesize with feedback
            END:       END,           # PASS | ESCALATE: return result
        },
    )

    compiled = graph.compile()
    logger.info("MARS graph compiled successfully")
    return compiled
