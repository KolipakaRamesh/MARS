import logging
from langgraph.graph import END
from backend.orchestration.state import AgentState

logger = logging.getLogger(__name__)


def route_after_research(state: AgentState) -> str:
    """
    After a research step:
    - If there are remaining subtasks → loop back to research
    - If all subtasks done, or an error occurred → proceed to analyst
    """
    if state.get("error"):
        return "analyst"  # forward best-effort research on error

    idx = state["current_subtask_index"]
    total = len(state["subtasks"])
    next_node = "research" if idx < total else "analyst"
    logger.info("[Router] Research status: %d/%d tasks complete. Next: %s", idx, total, next_node)
    return next_node


def route_after_review(state: AgentState) -> str:
    """
    After reviewer scores the answer:
    - PASS or ESCALATE → done (return to caller)
    - RETRY (within iteration budget) → re-run analyst with feedback

    Guard: iteration_count prevents infinite retry loops.
    """
    verdict = state.get("verdict", "PASS")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)

    if verdict == "RETRY" and iteration_count < max_iterations:
        logger.info("[Router] Verdict: RETRY (iter %d/%d). Returning to Analyst.", iteration_count, max_iterations)
        return "analyst"

    logger.info("[Router] Final verdict: %s. Terminating graph.", verdict)
    return END
