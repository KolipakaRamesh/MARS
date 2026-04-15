"""
MARS — Planner Agent.

Responsibility: Decompose the user's query into 2–5 ordered, atomic subtasks.

Design decisions:
  - Temperature: 0.0 (deterministic — same query should always produce same plan)
  - Output: strict JSON array of strings — parsed defensively
  - Fallback: if JSON fails twice, treat query itself as the single subtask
  - Uses the fastest/cheapest model since planning doesn't need deep reasoning
"""
import json
import logging
import re
from typing import Optional

from agents.base import BaseAgent
from llm import get_provider
from observability.tracer import trace_agent
from orchestration.state import AgentState
from config.settings import settings
from agents.prompts import PLANNER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)



class PlannerAgent(BaseAgent):
    name = "planner"
    description = "Decomposes queries into ordered research subtasks"

    def __init__(self):
        self.llm = get_provider(
            model=settings.planner_model,
            temperature=0.0,
            max_tokens=512,
        )

    @trace_agent("planner")
    def run(self, state: AgentState) -> dict:
        query = state["query"]
        logger.info("[Planner] Decomposing query: %s", query[:80])

        subtasks, usage = self._plan_with_usage(query)
        logger.info("[Planner] Generated %d subtasks", len(subtasks))

        return {
            "subtasks": subtasks,
            "current_subtask_index": 0,
            "llm_usage": [{"agent": "planner", **usage}],
            "agent_trace": [
                self._trace("plan_created", {"query": query, "subtasks": subtasks})
            ],
        }

    def _plan_with_usage(self, query: str, retries: int = 2) -> tuple:
        """Invoke LLM with usage tracking and parse JSON, with retry on parse failure."""
        last_usage = {"model": self.llm.model, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "latency_ms": 0}
        for attempt in range(retries):
            try:
                raw, usage = self.llm.invoke_with_usage(PLANNER_SYSTEM_PROMPT, query)
                last_usage = usage
                return self._parse_subtasks(raw), last_usage
            except (Exception) as exc:
                logger.warning("[Planner] Attempt %d failed: %s", attempt + 1, exc)
                if attempt == retries - 1:
                    logger.warning("[Planner] Falling back to single-subtask plan")
                    return [query], last_usage
        return [query], last_usage

    def _plan(self, query: str, retries: int = 2) -> list:
        """Legacy wrapper — returns subtasks only."""
        subtasks, _ = self._plan_with_usage(query, retries)
        return subtasks

    @staticmethod
    def _parse_subtasks(raw: str) -> list[str]:
        """Extract JSON array from LLM output (handles markdown code fences)."""
        # Strip markdown fences if present
        cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
        # Find first [...] block
        match = re.search(r"\[.*?\]", cleaned, re.DOTALL)
        if match:
            arr = json.loads(match.group())
        else:
            arr = json.loads(cleaned)

        if not isinstance(arr, list) or len(arr) == 0:
            raise ValueError("Expected non-empty JSON array")

        return [str(s).strip() for s in arr if s]
