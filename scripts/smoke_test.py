"""Quick smoke test for MARS system — validates all modules load and core utilities work."""
import sys
sys.path.insert(0, '.')

from config.settings import settings
from llm import get_provider
from orchestration.state import AgentState, initial_state
from orchestration.router import route_after_research, route_after_review
from orchestration.graph import build_graph
from tools.registry import build_default_registry
from tools.web_search import web_search
from tools.wiki_search import wiki_search
from tools.calculator import calculator
from tools.file_reader import file_reader
from memory.long_term import LongTermMemory
from memory.episodic import EpisodicMemory
from agents.base import BaseAgent
from agents.planner import PlannerAgent
from agents.analyst import AnalystAgent
from agents.reviewer import ReviewerAgent

print("All MARS modules imported successfully")

# Calculator (pure function, no external calls)
result = calculator("(2 ** 10) + (3 * 4)")
print(f"Calculator test: {result}")

# State factory
state = initial_state("What is quantum computing?", "test-session")
print(f"State factory test: session={state['session_id']}, query_len={len(state['query'])}")

# Tool registry
registry = build_default_registry()
tools = registry.list_tools()
print(f"Tool registry: {len(tools)} tools registered: {[t['name'] for t in tools]}")

# LLM provider factory (doesn't call API)
provider = get_provider(model="meta-llama/llama-3.2-3b-instruct", temperature=0.0)
print(f"LLM provider: {provider.model}")

print()
print("=" * 50)
print("MARS system validation PASSED")
print("=" * 50)
