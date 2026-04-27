"""
MARS — Abstract BaseAgent.

All agents share this contract:
  - Receive the full AgentState
  - Return a PARTIAL state dict (only changed keys)
  - Never mutate state directly — LangGraph merges the partial dict

This design keeps agents loosely coupled: they don't know about each other,
and can be unit-tested by passing a mock state dict.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from backend.orchestration.state import AgentState


class BaseAgent(ABC):
    """Minimal agent protocol."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, state: AgentState) -> dict:
        """
        Execute the agent's logic.

        Args:
            state: Full current AgentState (read-only by convention).

        Returns:
            Partial dict with only the keys this agent modifies.
            Example: {"synthesized_answer": "...", "agent_trace": [...]}
        """
        ...

    # ------------------------------------------------------------------
    # Helpers available to all agents
    # ------------------------------------------------------------------

    def _trace(self, event: str, data: dict | None = None) -> dict:
        """Build a standardized trace entry for agent_trace accumulator."""
        return {
            "agent":     self.name,
            "event":     event,
            "timestamp": datetime.utcnow().isoformat(),
            "data":      data or {},
        }

    def _error_state(self, message: str) -> dict:
        """Return a partial state that flags an error without crashing the graph."""
        return {
            "error": f"[{self.name}] {message}",
            "agent_trace": [self._trace("error", {"message": message})],
        }
