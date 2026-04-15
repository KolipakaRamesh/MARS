"""
MARS — Abstract LLM Provider.

Design: thin interface so any backend (OpenRouter, OpenAI, Anthropic, local)
can be swapped without touching agent code.
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class LLMProvider(ABC):
    """Minimal contract every LLM backend must implement."""

    @abstractmethod
    def invoke(self, system_prompt: str, user_message: str) -> str:
        """Single-turn call. Returns the assistant content string."""
        ...

    @abstractmethod
    def chat(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Multi-turn call.
        messages: [{"role": "user"|"assistant", "content": "..."}]
        Returns the next assistant content string.
        """
        ...
