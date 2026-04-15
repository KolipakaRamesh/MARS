"""
MARS — OpenRouter LLM Provider.

Uses the OpenAI-compatible API endpoint exposed by OpenRouter.
Supports every model available on openrouter.ai with zero code changes.
Retry logic via tenacity handles transient 429 / 5xx errors.
"""
import logging
import time
from typing import List, Dict

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from llm.provider import LLMProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """
    OpenAI-compatible client pointed at OpenRouter.

    Args:
        model:       OpenRouter model ID (e.g. "meta-llama/llama-3.1-8b-instruct")
        temperature: Sampling temperature (0.0 = deterministic)
        max_tokens:  Max tokens in the completion
    """

    def __init__(
        self,
        model: str = "meta-llama/llama-3.1-8b-instruct",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def invoke(self, system_prompt: str, user_message: str) -> str:
        """Single-turn convenience wrapper."""
        return self.chat(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

    def chat(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Multi-turn call — full message history passed to the model."""
        content, _ = self.chat_with_usage(system_prompt, messages)
        return content

    def chat_with_usage(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> tuple:
        """
        Multi-turn call that also returns a live usage record from OpenRouter.

        Returns:
            (content_str, usage_dict) where usage_dict contains:
                model, prompt_tokens, completion_tokens, total_tokens, latency_ms
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        t0 = time.perf_counter()
        response = self._call_with_retry(full_messages)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)

        usage_record = {
            "model":             self.model,
            "prompt_tokens":     getattr(usage, "prompt_tokens",     0) if usage else 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "total_tokens":      getattr(usage, "total_tokens",      0) if usage else 0,
            "latency_ms":        latency_ms,
        }

        logger.debug(
            "OpenRouter [%s] prompt=%d completion=%d total=%d latency=%.0fms",
            self.model,
            usage_record["prompt_tokens"],
            usage_record["completion_tokens"],
            usage_record["total_tokens"],
            latency_ms,
        )
        return content.strip(), usage_record

    def invoke_with_usage(self, system_prompt: str, user_message: str) -> tuple:
        """Single-turn call that also returns usage data."""
        return self.chat_with_usage(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_with_retry(self, messages: List[Dict[str, str]]):
        return self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra_headers={
                "HTTP-Referer": "https://github.com/mars-agent",
                "X-Title": "MARS Multi-Agent System",
            },
        )
