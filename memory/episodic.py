"""
MARS — Episodic Memory (Convex-backed).

Saves every completed research session to the Convex 'sessions' table.
Designed for:
  - Real-time updates to the UI history sidebar
  - Cross-device session persistence
  - Deep analytics via the Convex dashboard
"""
import logging
from datetime import datetime
from typing import Optional

from convex import ConvexClient
from config.settings import settings

logger = logging.getLogger(__name__)


class EpisodicMemory:
    def __init__(self, convex_url: Optional[str] = None):
        self.url = convex_url or settings.convex_url
        self._client = None

        if not self.url:
            logger.warning("Convex URL not configured. Episodic memory will be a no-op.")

    def _get_client(self) -> Optional[ConvexClient]:
        """Lazy-initialize the Convex client."""
        if self._client is not None:
            return self._client
        
        if not self.url:
            return None
            
        try:
            self._client = ConvexClient(self.url)
            return self._client
        except Exception as exc:
            logger.error("Failed to initialize Convex client: %s", exc)
            return None

    def log(self, state: dict) -> None:
        """Log a completed session to Convex."""
        client = self._get_client()
        if not client:
            return

        entry = {
            "session_id":        state.get("session_id", "unknown"),
            "query":             state.get("query", ""),
            "subtasks":          state.get("subtasks", []),
            "synthesized_answer": state.get("synthesized_answer", ""),
            "quality_score":     float(state.get("quality_score", 0.0)),
            "verdict":           state.get("verdict", ""),
            "iteration_count":   int(state.get("iteration_count", 0)),
            "timestamp":         datetime.utcnow().isoformat(),
        }

        if state.get("error"):
            entry["error"] = state.get("error")

        try:
            client.mutation("sessions:logSession", entry)
            logger.info("Episodic session logged to Convex: '%s'", entry["session_id"])
        except Exception as exc:
            logger.warning("Failed to log session to Convex: %s", exc)

    def recent_sessions(self, n: int = 10) -> list[dict]:
        """Return the N most recent session records via Convex query."""
        client = self._get_client()
        if not client:
            return []

        try:
            return client.query("sessions:getRecentSessions", {"limit": n})
        except Exception as exc:
            logger.warning("Failed to fetch sessions from Convex: %s", exc)
            return []
