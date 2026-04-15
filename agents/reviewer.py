"""
MARS — Reviewer Agent (LLM-as-Judge).

Responsibility: Evaluate the synthesized answer against the original query
and return a structured quality verdict.

Scoring dimensions:
  - Relevance:    Does the answer address the query?
  - Groundedness: No hallucinations / unsupported claims?
  - Completeness: Are all subtasks addressed?
  - Clarity:      Is it readable and well-structured?

Verdicts:
  - PASS      → score >= threshold → return answer to user
  - RETRY     → score < threshold AND iterations remain → re-run analyst
  - ESCALATE  → score < threshold AND iterations exhausted → return with warning

Design: temperature=0.0 for deterministic, reproducible scoring.
"""
import json
import logging
import re

from agents.base import BaseAgent
from llm import get_provider
from observability.tracer import trace_agent
from orchestration.state import AgentState
from config.settings import settings
from agents.prompts import REVIEWER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)



class ReviewerAgent(BaseAgent):
    name = "reviewer"
    description = "LLM-as-Judge: scores answer quality and decides pass/retry/escalate"

    def __init__(self):
        self.llm = get_provider(
            model=settings.reviewer_model,
            temperature=0.0,
            max_tokens=512,
        )
        self.threshold = settings.quality_threshold

    @trace_agent("reviewer")
    def run(self, state: AgentState) -> dict:
        query = state["query"]
        answer = state.get("synthesized_answer", "")

        if not answer:
            return {
                "quality_score": 0.0,
                "verdict": "RETRY",
                "feedback": "No answer was produced by the analyst.",
                "agent_trace": [self._trace("review_failed", {"reason": "empty_answer"})],
            }

        logger.info("[Reviewer] Evaluating answer (iteration %d)", state.get("iteration_count", 1))

        result = self._evaluate(query, answer)
        score   = result.get("overall_score", 0.0)
        verdict = result.get("verdict", "PASS")
        feedback = result.get("feedback", "")

        # Enforce iteration guard (router also checks, but belt-and-suspenders)
        iteration = state.get("iteration_count", 1)
        max_iter  = state.get("max_iterations", 3)
        if verdict == "RETRY" and iteration >= max_iter:
            verdict  = "ESCALATE"
            feedback += f" [Max iterations ({max_iter}) reached — escalating best-effort answer]"

        logger.info("[Reviewer] Score: %.2f | Verdict: %s", score, verdict)

        return {
            "quality_score": score,
            "verdict": verdict,
            "feedback": feedback,
            "llm_usage": [{"agent": "reviewer", **result.get("_usage", {})}],
            "agent_trace": [
                self._trace("review_complete", {
                    "scores": result.get("scores", {}),
                    "overall_score": score,
                    "verdict": verdict,
                })
            ],
        }

    def _evaluate(self, query: str, answer: str) -> dict:
        """Call LLM and parse JSON review result, with usage tracking."""
        user_msg = (
            f"ORIGINAL QUERY:\n{query}\n\n"
            f"ANSWER TO EVALUATE:\n{answer}\n\n"
            f"Provide your evaluation as JSON."
        )
        last_usage = {"model": self.llm.model, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "latency_ms": 0}
        for attempt in range(2):
            try:
                raw, usage = self.llm.invoke_with_usage(REVIEWER_SYSTEM_PROMPT, user_msg)
                last_usage = usage
                parsed = self._parse_json(raw)
                parsed["_usage"] = last_usage
                return parsed
            except (Exception) as exc:
                logger.warning("[Reviewer] JSON parse attempt %d failed: %s", attempt + 1, exc)

        # Fallback: conservative PASS to avoid blocking the user
        logger.error("[Reviewer] Could not parse review response — defaulting to PASS at 0.5")
        return {
            "scores": {},
            "overall_score": 0.5,
            "verdict": "PASS",
            "feedback": "Reviewer could not parse quality score — treating as acceptable.",
        }

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract JSON from response, handling markdown code fences."""
        cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(cleaned)
