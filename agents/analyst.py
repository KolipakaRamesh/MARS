"""
MARS — Analyst Agent.

Responsibility: Synthesize all raw research chunks into a single, coherent,
structured markdown answer.

Design decisions:
  - Uses the largest/most capable model in the system (70B parameter class)
  - Temperature: 0.3 (some creativity for prose quality, but grounded)
  - Accepts reviewer feedback on RETRY passes to improve the answer
  - Strict grounding instruction: "Do NOT add information not in research"

Token budget: raw_research can be long; we chunk if needed but pass all context
to the analyst since synthesis quality depends on complete information.
"""
import logging

from agents.base import BaseAgent
from llm import get_provider
from observability.tracer import trace_agent
from orchestration.state import AgentState
from config.settings import settings
from agents.prompts import ANALYST_SYSTEM_PROMPT, ANALYST_RETRY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)



class AnalystAgent(BaseAgent):
    name = "analyst"
    description = "Synthesizes raw research into a structured, grounded answer"

    def __init__(self):
        self.llm = get_provider(
            model=settings.analyst_model,
            temperature=0.3,
            max_tokens=1024,
        )

    @trace_agent("analyst")
    def run(self, state: AgentState) -> dict:
        iteration = state.get("iteration_count", 0)
        logger.info("[Analyst] Synthesizing (iteration %d)", iteration)

        raw_research = state.get("raw_research", [])
        if not raw_research:
            return self._error_state("No research data to synthesize")

        research_block = "\n\n".join(raw_research)
        query = state["query"]

        # On RETRY, incorporate reviewer feedback
        feedback = state.get("feedback", "")
        if iteration > 0 and feedback:
            system = ANALYST_RETRY_SYSTEM_PROMPT.format(feedback=feedback)
            logger.info("[Analyst] Retry pass with reviewer feedback")
        else:
            system = ANALYST_SYSTEM_PROMPT

        user_msg = (
            f"ORIGINAL QUERY:\n{query}\n\n"
            f"RAW RESEARCH NOTES:\n{research_block}\n\n"
            f"Synthesize a complete answer now."
        )
        if iteration > 0 and feedback and state.get("synthesized_answer"):
            user_msg = (
                f"ORIGINAL QUERY:\n{query}\n\n"
                f"YOUR PREVIOUS ANSWER:\n{state['synthesized_answer']}\n\n"
                f"RAW RESEARCH NOTES:\n{research_block}\n\n"
                f"Revise your answer to address the feedback."
            )

        answer, usage = self.llm.invoke_with_usage(system, user_msg)

        return {
            "synthesized_answer": answer,
            "iteration_count": iteration + 1,
            "llm_usage": [{"agent": "analyst", **usage}],
            "agent_trace": [
                self._trace("synthesis_complete", {
                    "iteration": iteration,
                    "is_retry": iteration > 0,
                    "answer_length": len(answer),
                })
            ],
        }
