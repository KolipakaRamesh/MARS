"""
MARS — Opik Observability Integration.

Provides a decorator `@trace_agent(name)` that wraps any agent's run() method
with an Opik span, capturing:
  - Input state (query, subtask index)
  - Output (partial state diff)
  - Duration
  - Errors

Graceful degradation: if Opik is not configured or unavailable, the decorator
is a no-op and the agent runs without instrumentation.
"""
import logging
import time
import functools
from typing import Callable

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# ── Opik initialization ───────────────────────────────────────────────────────
_opik_enabled = False

try:
    import opik

    opik.configure(
        api_key=settings.opik_api_key,
        project_name=settings.opik_project_name,
        workspace=settings.opik_workspace,
        url_override=settings.opik_url_override,
        use_local=settings.opik_use_local,
    )
    _opik_enabled = True
    logger.info("Opik observability initialized (project: %s)", settings.opik_project_name)
except Exception as exc:
    logger.warning("Opik not available — running without traces: %s", exc)


# ── Decorator ─────────────────────────────────────────────────────────────────

def trace_agent(span_name: str) -> Callable:
    """
    Decorator for agent run() methods.

    Usage:
        @trace_agent("planner")
        def run(self, state: AgentState) -> dict:
            ...

    Captures:
        - span name and agent class name
        - input: query, session_id, current_subtask_index
        - output: keys modified by this agent
        - latency
        - any exception (re-raised after recording)
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, state, *args, **kwargs):
            if not _opik_enabled:
                return fn(self, state, *args, **kwargs)

            start = time.perf_counter()
            span_input = {
                "agent":               span_name,
                "query":               state.get("query", ""),
                "session_id":          state.get("session_id", ""),
                "subtask_index":       state.get("current_subtask_index", 0),
                "iteration_count":     state.get("iteration_count", 0),
            }

            try:
                with opik.start_as_current_span(name=span_name, input=span_input) as span:
                    result = fn(self, state, *args, **kwargs)
                    latency_ms = (time.perf_counter() - start) * 1000
                    
                    from opik.opik_context import update_current_span
                    update_current_span(output={
                        "keys_modified": list(result.keys()),
                        "latency_ms":    round(latency_ms, 2),
                    })
                    return result
            except Exception as exc:
                logger.error("[%s] Exception in traced agent: %s", span_name, exc)
                raise

        return wrapper
    return decorator


def trace_tool_call(tool_name: str, tool_input: str, result: str, duration_ms: float):
    """Log a tool invocation as an Opik event (call from ResearchAgent)."""
    if not _opik_enabled:
        return
    try:
        opik.log_event(
            name=f"tool:{tool_name}",
            metadata={
                "tool":        tool_name,
                "input":       tool_input[:200],
                "result":      result[:500],
                "duration_ms": round(duration_ms, 2),
            },
        )
    except Exception as exc:
        logger.debug("trace_tool_call failed (non-critical): %s", exc)
