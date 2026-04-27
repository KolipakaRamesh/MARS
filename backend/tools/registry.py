"""
MARS — Tool Registry.

Tools are functions (sync or async) registered by name. The ResearchAgent queries
this registry to discover available tools and their descriptions,
which are injected into the ReAct system prompt.

Design:
  - Each tool is a Python function (str → str or str → awaitable str)
  - Tools have no state — safe to call concurrently
  - Registration is explicit — no magical auto-discovery
"""
import asyncio
from typing import Callable, Dict, Any, Union, Coroutine, List
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, fn: Union[Callable[[str], str], Callable[[str], Coroutine[Any, Any, str]]], description: str) -> None:
        """Register a tool by name."""
        self._tools[name] = {"fn": fn, "description": description}
        logger.debug("Tool registered: %s", name)

    def get(self, name: str) -> Any | None:
        """Return the tool entry or None if not found."""
        return self._tools.get(name)

    async def call(self, name: str, input_str: str) -> str:
        """Execute a tool by name, handling both sync and async functions."""
        entry = self._tools.get(name)
        if not entry:
            return f"Tool '{name}' not found."
        
        fn = entry["fn"]
        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn(input_str)
            else:
                return fn(input_str)
        except Exception as exc:
            logger.error("Error executing tool '%s': %s", name, exc)
            return f"Error executing tool '{name}': {str(exc)}"

    def list_tools(self) -> list[dict]:
        """Return [{name, description}] for all registered tools."""
        return [
            {"name": k, "description": v["description"]}
            for k, v in self._tools.items()
        ]

    def tool_descriptions_for_prompt(self) -> str:
        """Format tool list for injection into ReAct system prompt."""
        lines = []
        for t in self.list_tools():
            lines.append(f"  - {t['name']}: {t['description']}")
        return "\n".join(lines)

    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


def build_default_registry() -> ToolRegistry:
    """Factory — builds registry with all default MARS tools pre-registered."""
    from backend.tools.web_search import web_search
    from backend.tools.wiki_search import wiki_search
    from backend.tools.calculator import calculator
    from backend.tools.file_reader import file_reader

    registry = ToolRegistry()
    registry.register(
        "web_search",
        web_search,
        "Search the web for recent information. Input: a search query string.",
    )
    registry.register(
        "wiki_search",
        wiki_search,
        "Search Wikipedia for factual background on a topic. Input: a topic name.",
    )
    registry.register(
        "calculator",
        calculator,
        "Evaluate a mathematical expression. Input: an expression like '2 + 2 * 10'.",
    )
    registry.register(
        "file_reader",
        file_reader,
        "CRITICAL: Use this for ANY local file path. Input: absolute path with forward slashes (e.g., C:/Users/file.txt).",
    )
    
    # ── MCP Tools Placeholder ─────────────────────────────────────────────
    # In a full implementation, we would loop over configured MCP servers 
    # and register their tools here. For now, we've enabled the infrastructure.
    
    return registry
