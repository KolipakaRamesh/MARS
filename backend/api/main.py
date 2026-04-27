"""
MARS — FastAPI Application.

Exposes REST endpoints for running the multi-agent pipeline.
All heavy objects (graph, agents, memory) are initialized once at startup
and reused across requests via FastAPI's lifespan mechanism.
"""
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.agents.planner import PlannerAgent
from backend.agents.analyst import AnalystAgent
from backend.agents.reviewer import ReviewerAgent
from backend.agents.research import ResearchAgent
from backend.memory.long_term import LongTermMemory
from backend.memory.episodic import EpisodicMemory
from backend.orchestration.graph import build_graph
from backend.orchestration.state import initial_state
from backend.tools.registry import build_default_registry
from backend.config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Shared singletons ─────────────────────────────────────────────────────────
_graph = None
_long_term_memory = None
_episodic_memory = None

# Calculate absolute path to frontend/dist
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all singletons on startup, clean up on shutdown."""
    global _graph, _long_term_memory, _episodic_memory
    logger.info("MARS starting up...")

    _long_term_memory = LongTermMemory()
    _episodic_memory  = EpisodicMemory()
    tool_registry     = build_default_registry()

    planner  = PlannerAgent()
    research = ResearchAgent(tool_registry, _long_term_memory)
    analyst  = AnalystAgent()
    reviewer = ReviewerAgent()

    _graph = build_graph(planner, research, analyst, reviewer)
    logger.info("MARS ready ✓")
    yield
    logger.info("MARS shutting down")


app = FastAPI(
    title="MARS — Multi-Agent Research System",
    description="Local-first, graph-orchestrated multi-agent research pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="The research question")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    max_iterations: int = Field(default=3, ge=1, le=5)


class QueryResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    quality_score: float
    verdict: str
    subtasks: list[str]
    iteration_count: int
    llm_usage: list[dict] = []
    error: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "system": "MARS", "graph_ready": _graph is not None}


@app.post("/run", response_model=QueryResponse)
async def run_query(req: QueryRequest):
    """Execute the full multi-agent pipeline with live heartbeats to Convex."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="System not initialized")

    state = initial_state(req.query, req.session_id)
    state["max_iterations"] = req.max_iterations

    from convex import ConvexClient
    convex = None
    if settings.convex_url:
        try:
            convex = ConvexClient(settings.convex_url)
        except Exception as exc:
            logger.warning("Failed to init Convex client for heartbeats: %s", exc)

    final_state = state
    try:
        # Use astream() to track execution stage by stage
        async for output in _graph.astream(state):
            for node_name, node_output in output.items():
                logger.info("[Graph] Enter node: %s", node_name)
                
                # Push heartbeat to Convex
                if convex:
                    try:
                        status_msg = f"Agent '{node_name}' is processing..."
                        subtask_idx = node_output.get("current_subtask_index")

                        heartbeat_data = {
                            "session_id": req.session_id,
                            "agent": node_name,
                            "status": status_msg,
                        }
                        if subtask_idx is not None:
                            heartbeat_data["subtask_index"] = subtask_idx

                        # After planner runs, stream its subtasks to Convex so
                        # the frontend can display them immediately
                        if node_name == "planner" and node_output.get("subtasks"):
                            heartbeat_data["subtasks"] = node_output["subtasks"]

                        convex.mutation("heartbeats:update", heartbeat_data)
                    except Exception as exc:
                        logger.debug("Heartbeat push failed: %s", exc)

                # Accumulate the final state
                final_state = {**final_state, **node_output}

    except Exception as exc:
        logger.error("Graph execution failed: %s", exc, exc_info=True)
        # Clear heartbeat on error
        if convex:
            convex.mutation("heartbeats:update", {
                "session_id": req.session_id,
                "agent": "error",
                "status": f"Error: {str(exc)}"
            })
        raise HTTPException(status_code=500, detail=str(exc))

    # Clear heartbeat on completion
    if convex:
        try:
            convex.mutation("heartbeats:update", {
                "session_id": req.session_id,
                "agent": "done",
                "status": "Research complete ✓"
            })
        except: pass

    # Store to long-term memory if quality is sufficient
    _long_term_memory.store(
        session_id=final_state["session_id"],
        query=final_state["query"],
        content=final_state["synthesized_answer"],
        quality_score=final_state["quality_score"],
    )

    # Log episode
    _episodic_memory.log(final_state)

    return QueryResponse(
        session_id=final_state["session_id"],
        query=final_state["query"],
        answer=final_state["synthesized_answer"],
        quality_score=final_state["quality_score"],
        verdict=final_state["verdict"],
        subtasks=final_state["subtasks"],
        iteration_count=final_state["iteration_count"],
        llm_usage=final_state.get("llm_usage", []),
        error=final_state.get("error"),
    )

# ── Serve Frontend ────────────────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    from fastapi.responses import FileResponse
    index_path = FRONTEND_DIR / index.html
    if not index_path.exists():
        return {"error": f"Frontend not found at {index_path}. Did you run 'npm run build'?"}
    return FileResponse(index_path)

# Mount remaining assets (css, js, etc)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    logger.warning("Frontend directory not found at %s", FRONTEND_DIR)
