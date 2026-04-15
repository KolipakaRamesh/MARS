"""
MARS — Tool Registry.

Tools are pure functions registered by name. The ResearchAgent queries
this registry to discover available tools and their descriptions,
which are injected into the ReAct system prompt.

Design:
  - Each tool is a plain Python function (str → str)
  - Tools have no state — safe to call concurrently
  - Registration is explicit — no magical auto-discovery
"""
from typing import Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, fn: Callable[[str], str], description: str) -> None:
        """Register a tool by name."""
        self._tools[name] = {"fn": fn, "description": description}
        logger.debug("Tool registered: %s", name)

    def get(self, name: str) -> Callable[[str], str] | None:
        """Return the tool function or None if not found."""
        entry = self._tools.get(name)
        return entry["fn"] if entry else None

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
    from tools.web_search import web_search
    from tools.wiki_search import wiki_search
    from tools.calculator import calculator
    from tools.file_reader import file_reader

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
        "Read the contents of a local file. Input: absolute or relative file path.",
    )
    return registry
