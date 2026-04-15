"""
MARS — Research Agent.

Responsibility: Execute a single subtask using a ReAct (Reason+Act) loop.

ReAct pattern:
  1. LLM reasons about what tool to call
  2. Tool is executed → observation returned
  3. LLM reasons about next step given the observation
  4. Loop until LLM writes "Final Answer:" or max_steps reached

Why text-based ReAct (not function-calling)?
  - Works reliably with any OpenRouter model (including smaller free-tier models)
  - No model-specific function-calling API required
  - Transparent: every reasoning step is visible in the trace

Memory injection: Past similar research is retrieved from Pinecone and prepended
to the subtask context so the agent avoids re-researching known facts.
"""
import logging
import re
from typing import Optional

from agents.base import BaseAgent
from llm import get_provider
from memory.long_term import LongTermMemory
from observability.tracer import trace_agent
from orchestration.state import AgentState
from tools.registry import ToolRegistry
from config.settings import settings
from agents.prompts import RESEARCH_REACT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)




class ResearchAgent(BaseAgent):
    name = "research"
    description = "Executes subtasks via ReAct tool-use loop"

    def __init__(self, tool_registry: ToolRegistry, memory: LongTermMemory):
        self.tool_registry = tool_registry
        self.memory = memory
        self.llm = get_provider(
            model=settings.research_model,
            temperature=0.2,
            max_tokens=1024,
        )
        self.max_steps = settings.max_react_steps

    @trace_agent("research")
    def run(self, state: AgentState) -> dict:
        idx = state["current_subtask_index"]
        subtask = state["subtasks"][idx]

        logger.info("[Research] Subtask %d/%d: %s", idx + 1, len(state["subtasks"]), subtask[:80])

        # Retrieve relevant past research from long-term memory
        memory_snippets = self.memory.retrieve(subtask)
        memory_context = self._format_memory(memory_snippets)

        # Execute ReAct loop
        result, usage = self._react_loop(subtask, memory_context)

        return {
            "raw_research": [f"=== Subtask {idx + 1}: {subtask} ===\n{result}"],
            "current_subtask_index": idx + 1,
            "llm_usage": [{"agent": "research", **usage}],
            "agent_trace": [
                self._trace("subtask_complete", {
                    "subtask_index": idx,
                    "subtask": subtask,
                    "result_length": len(result),
                    "memory_hits": len(memory_snippets),
                })
            ],
        }

    # ------------------------------------------------------------------
    # ReAct Loop
    # ------------------------------------------------------------------

    def _react_loop(self, subtask: str, memory_context: str) -> tuple:
        """
        Multi-turn conversation implementing the ReAct pattern.
        Returns (answer_str, aggregated_usage_dict).
        """
        system = RESEARCH_REACT_SYSTEM_PROMPT.format(
            tool_descriptions=self.tool_registry.tool_descriptions_for_prompt(),
            tool_names=", ".join(self.tool_registry.tool_names()),
        )

        messages = []
        user_content = subtask
        if memory_context:
            user_content = f"RELEVANT PAST RESEARCH:\n{memory_context}\n\nCURRENT SUBTASK:\n{subtask}"

        messages.append({"role": "user", "content": user_content})

        # Aggregate token usage across all steps
        agg_usage = {
            "model": self.llm.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "latency_ms": 0.0,
        }

        for step in range(self.max_steps):
            response, step_usage = self.llm.chat_with_usage(system, messages)
            # Accumulate usage
            agg_usage["prompt_tokens"]     += step_usage.get("prompt_tokens", 0)
            agg_usage["completion_tokens"] += step_usage.get("completion_tokens", 0)
            agg_usage["total_tokens"]      += step_usage.get("total_tokens", 0)
            agg_usage["latency_ms"]        += step_usage.get("latency_ms", 0)

            messages.append({"role": "assistant", "content": response})

            # Check if agent reached a conclusion
            if "Final Answer:" in response:
                answer = response.split("Final Answer:", 1)[-1].strip()
                logger.debug("[Research] Final Answer reached at step %d", step + 1)
                return answer, agg_usage

            # Parse and execute tool call
            tool_name, tool_input = self._parse_action(response)

            if tool_name is None:
                logger.warning("[Research] Could not parse Action at step %d", step + 1)
                messages.append({
                    "role": "user",
                    "content": "Please continue following the format: Thought / Action / Action Input, then Final Answer."
                })
                continue

            # Execute tool
            tool_fn = self.tool_registry.get(tool_name)
            if tool_fn:
                logger.debug("[Research] Calling tool '%s' with input: %s", tool_name, tool_input[:80])
                observation = tool_fn(tool_input)
            else:
                observation = f"Tool '{tool_name}' not found. Available: {', '.join(self.tool_registry.tool_names())}"

            messages.append({
                "role": "user",
                "content": f"Observation: {observation}\n\nContinue your research."
            })

        # Fallback: return best-effort result + accumulated usage
        logger.warning("[Research] Max steps reached, returning best-effort result")
        return self._extract_best_effort(messages), agg_usage

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_action(text: str) -> tuple[Optional[str], str]:
        """
        Extract (tool_name, tool_input) from a ReAct-formatted response.
        Returns (None, "") if no Action block found.
        """
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text)
        input_match  = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text, re.DOTALL)

        if not action_match:
            return None, ""

        tool_name  = action_match.group(1).strip()
        tool_input = input_match.group(1).strip() if input_match else ""
        return tool_name, tool_input

    @staticmethod
    def _format_memory(snippets: list[str]) -> str:
        if not snippets:
            return ""
        parts = [f"[Memory {i+1}] {s}" for i, s in enumerate(snippets)]
        return "\n\n".join(parts)

    @staticmethod
    def _extract_best_effort(messages: list[dict]) -> str:
        """When max steps exceeded, return the last assistant message."""
        for msg in reversed(messages):
            if msg["role"] == "assistant":
                return msg["content"]
        return "Research incomplete: no results gathered."
