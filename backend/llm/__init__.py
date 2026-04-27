"""LLM package. Default export: get_provider factory."""
from backend.llm.openrouter_provider import OpenRouterProvider


def get_provider(model: str, temperature: float = 0.1, max_tokens: int = 1024) -> OpenRouterProvider:
    """Factory — returns an OpenRouter provider. Swap implementation here to change backends."""
    return OpenRouterProvider(model=model, temperature=temperature, max_tokens=max_tokens)
