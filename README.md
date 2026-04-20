# MARS — Multi-Agent Research System

> **Production-grade, graph-orchestrated multi-agent research pipeline**
> LLM Gateway: OpenRouter · Real-time Backend: Convex · Orchestration: LangGraph · Observability: Opik

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange)](https://langchain-ai.github.io/langgraph/)
[![Convex](https://img.shields.io/badge/Convex-Backend-purple)](https://convex.dev)

**Repository:** [github.com/KolipakaRamesh/MARS](https://github.com/KolipakaRamesh/MARS)

---

## What is MARS?

MARS is a **multi-agent AI research assistant** that answers complex, open-ended questions by deploying a team of four specialized AI agents. Instead of a single LLM trying to answer everything at once, MARS divides the problem — **plan → research → synthesize → review** — with each agent doing what it does best.

### The Core Problem MARS Solves

When you ask a single LLM a complex research question, you get:
- Hallucinated facts with no grounding
- Shallow, unverified answers
- No self-correction mechanism
- No real-world data retrieval

MARS solves this with:
- **Structured decomposition** — breaks big questions into atomic subtasks
- **Grounded research** — live web & Wikipedia search, no hallucination
- **Quality gating** — scored review with automatic retry if quality is low
- **Semantic memory** — reuses past research via vector search to avoid redundant work
- **Real-time transparency** — live agent status tracking visible in the browser UI

---

## System Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         USER INTERACTION LAYER                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌──────────────────────────────────────────────────────────────────┐   ║
║   │               React Frontend (Vite + JSX)                        │   ║
║   │                                                                  │   ║
║   │  ┌────────────────┐  ┌───────────────────┐  ┌────────────────┐  │   ║
║   │  │  Search Bar    │  │ Live Status Bar   │  │ Session History│  │   ║
║   │  │  (query input) │  │ (Convex useQuery) │  │ (Convex live)  │  │   ║
║   │  └────────────────┘  └───────────────────┘  └────────────────┘  │   ║
║   │                                                                  │   ║
║   │  ┌─────────────────────────────────────────────────────────┐    │   ║
║   │  │   Research Plan Sidebar  │  LLM Token Usage Metrics     │    │   ║
║   │  │   (subtask breakdown)    │  (per-agent breakdown)       │    │   ║
║   │  └─────────────────────────────────────────────────────────┘    │   ║
║   │                                                                  │   ║
║   │   POST /run ──────────────────────────────────────────────────►  │   ║
║   │   ◄─────────── JSON Response (answer, score, verdict, usage) ──  │   ║
║   └──────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                         CONVEX REAL-TIME LAYER                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌──────────────────────────────────────────────────────────────────┐   ║
║   │                     Convex Cloud Backend                         │   ║
║   │                                                                  │   ║
║   │  ┌────────────────┐  ┌───────────────────┐  ┌────────────────┐  │   ║
║   │  │  heartbeats    │  │     sessions      │  │ research_memory│  │   ║
║   │  │  (live status) │  │ (episodic memory) │  │ (vector RAG)   │  │   ║
║   │  │                │  │                   │  │  1536-dim idx  │  │   ║
║   │  │  agent: str    │  │ query, answer,    │  │  content +     │  │   ║
║   │  │  status: str   │  │ score, verdict    │  │  embedding[]   │  │   ║
║   │  │  last_updated  │  │ subtasks[]        │  │  ttl_expires   │  │   ║
║   │  └────────────────┘  └───────────────────┘  └────────────────┘  │   ║
║   │        ▲ mutation            ▲ mutation           ▲ mutation      │   ║
║   │        │                    │                    │               │   ║
║   └──────────────────────────────────────────────────────────────────┘   ║
║                │                    │                    │               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                      FASTAPI APPLICATION LAYER                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌──────────────────────────────────────────────────────────────────┐   ║
║   │                     FastAPI Server (:8000)                       │   ║
║   │                                                                  │   ║
║   │   GET  /health   ── System status check                          │   ║
║   │   POST /run      ── Execute full agent pipeline (main endpoint)  │   ║
║   │   GET  /sessions ── Fetch recent sessions from Convex            │   ║
║   │   GET  /         ── Serves frontend/dist (static build)          │   ║
║   │                                                                  │   ║
║   │   Lifespan: Initializes all agents, memory, tools at startup     │   ║
║   │   Singleton: Graph compiled once, reused for all requests        │   ║
║   └───────────────────────────┬──────────────────────────────────────┘   ║
║                               │ graph.stream(state)                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║                       LANGGRAPH PIPELINE LAYER                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │                    LangGraph StateGraph                          │    ║
║   │                                                                  │    ║
║   │   ┌─────────────────────────────────────────────────────────┐   │    ║
║   │   │                    AgentState (Blackboard)               │   │    ║
║   │   │                                                          │   │    ║
║   │   │  query          session_id        max_iterations         │   │    ║
║   │   │  subtasks[]     current_subtask   raw_research[]         │   │    ║
║   │   │  synthesized_answer               quality_score          │   │    ║
║   │   │  verdict        feedback          iteration_count        │   │    ║
║   │   │  llm_usage[]    agent_trace[]     error                  │   │    ║
║   │   └─────────────────────────────────────────────────────────┘   │    ║
║   │                                                                  │    ║
║   │  ┌─────────┐   subtasks    ┌──────────────────────────────────┐ │    ║
║   │  │         │──────────────►│         Research Loop            │ │    ║
║   │  │ PLANNER │               │  ┌──────────────────────────┐    │ │    ║
║   │  │  Agent  │               │  │      RESEARCH Agent      │    │ │    ║
║   │  │         │               │  │   (ReAct Reasoning Loop) │    │ │    ║
║   │  │ llama   │               │  │                          │    │ │    ║
║   │  │ 3.2-3b  │               │  │  Thought → Action →      │    │ │    ║
║   │  │ temp=0  │               │  │  Action Input →          │    │ │    ║
║   │  │ 512 tok │               │  │  Observation (tool call) │    │ │    ║
║   │  └─────────┘               │  │  → Final Answer          │    │ │    ║
║   │       │                    │  └──────────┬───────────────┘    │ │    ║
║   │       │ entry              │             │  tool calls         │ │    ║
║   │       ▼                   │  ┌──────────▼───────────────┐    │ │    ║
║   │   set_entry_point          │  │      Tool Registry       │    │ │    ║
║   │                            │  │  web_search / wiki_search│    │ │    ║
║   │                            │  │  calculator / file_reader│    │ │    ║
║   │                            │  └──────────────────────────┘    │ │    ║
║   │                            │             │ idx < total?        │ │    ║
║   │                            └─────────────┼────────────────────┘ │    ║
║   │                                          │ route_after_research   │    ║
║   │                                    idx==total                    │    ║
║   │                                          │                       │    ║
║   │                                    ┌─────▼──────┐               │    ║
║   │                                    │  ANALYST   │               │    ║
║   │                                    │   Agent    │               │    ║
║   │                                    │ llama-70b  │               │    ║
║   │                                    │  temp=0.3  │               │    ║
║   │                                    │  2048 tok  │               │    ║
║   │                                    └─────┬──────┘               │    ║
║   │                                          │ synthesized_answer    │    ║
║   │                                    ┌─────▼──────┐               │    ║
║   │                                    │  REVIEWER  │               │    ║
║   │                                    │   Agent    │               │    ║
║   │                        ┌──RETRY ◄──│  llama-8b  │              │    ║
║   │                        │           │  temp=0.0  │               │    ║
║   │                        │           │  score 0→1 │               │    ║
║   │                        │           └─────┬──────┘               │    ║
║   │                        │                 │ PASS / ESCALATE       │    ║
║   │                        │           ┌─────▼──────┐               │    ║
║   │                        └──────────►│    END     │               │    ║
║   │                                    └────────────┘               │    ║
║   └──────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                        INFRASTRUCTURE LAYER                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  ║
║   │  OpenRouter API  │  │   Opik (Comet)   │  │    Convex Vector DB   │  ║
║   │                  │  │                  │  │                       │  ║
║   │ LLM gateway for  │  │  Full trace per  │  │  1536-dim embeddings  │  ║
║   │ any model via    │  │  agent run:      │  │  (text-embedding-3-   │  ║
║   │ OpenAI-compat    │  │  • input/output  │  │   small via OpenRouter│  ║
║   │ API. Retry via   │  │  • latency       │  │  90-day TTL policy    │  ║
║   │ tenacity (3x)    │  │  • tool calls    │  │  top-3 retrieval      │  ║
║   │                  │  │  • errors        │  │                       │  ║
║   └─────────────────┘  └──────────────────┘  └───────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## How A Research Request Flows End-to-End

Here is a step-by-step walkthrough of what happens when you type a query and press **Execute**:

```
User types: "What are the latest advances in quantum computing?"
                │
                ▼
  React Frontend sends POST /run to FastAPI
  { query: "...", session_id: "mars-1234", max_iterations: 3 }
                │
                ▼
  FastAPI creates initial AgentState and calls graph.stream(state)
  ┌─────────────────────────────────────────────────────────────┐
  │  STEP 1: PLANNER                                            │
  │  Model: llama-3.2-3b (temp=0.0, deterministic)             │
  │  Output JSON array of 2-5 subtasks:                         │
  │  [                                                          │
  │    "Find recent 2023-2024 milestones in quantum hardware",  │
  │    "Explain error correction advances in quantum systems",   │
  │    "Compare IBM vs Google vs IonQ quantum roadmaps"         │
  │  ]                                                          │
  │  ► Heartbeat pushed to Convex: "planner is processing..."   │
  └─────────────────────────────────────────────────────────────┘
                │
                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STEP 2: RESEARCH LOOP (repeats per subtask)                │
  │  Model: llama-3.1-8b (temp=0.2)                            │
  │                                                             │
  │  Before each subtask:                                       │
  │    → Query Convex vector index for similar past research    │
  │    → Inject matching snippets as context (RAG)              │
  │                                                             │
  │  ReAct loop for each subtask:                               │
  │    Thought: "I need to find recent quantum hardware news"   │
  │    Action: web_search                                       │
  │    Action Input: "quantum computing 2024 breakthroughs"     │
  │    Observation: [DuckDuckGo results]                        │
  │    Thought: "Let me also check Wikipedia for background"    │
  │    Action: wiki_search                                       │
  │    Action Input: "quantum computing"                         │
  │    Observation: [Wikipedia article summary]                  │
  │    Thought: "I now have enough info"                        │
  │    Final Answer: [compiled research findings]               │
  │                                                             │
  │  ► Heartbeat: "research is processing... subtask 1/3"       │
  └─────────────────────────────────────────────────────────────┘
                │
                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STEP 3: ANALYST                                            │
  │  Model: llama-3.3-70b (temp=0.3, max_tokens=2048)         │
  │  Input: all raw_research[] chunks concatenated             │
  │  Output: structured markdown answer with:                   │
  │    # Answer to: ...                                         │
  │    ## Summary                                               │
  │    ## Detailed Findings                                     │
  │    ## Key Takeaways                                         │
  │    ## Limitations                                           │
  │  ► Heartbeat: "analyst is processing..."                    │
  └─────────────────────────────────────────────────────────────┘
                │
                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STEP 4: REVIEWER (LLM-as-Judge)                           │
  │  Model: llama-3.1-8b (temp=0.0, deterministic scoring)    │
  │  Scores 4 dimensions (each 0.0-1.0):                       │
  │    relevance    = 0.90  (answers the question?)            │
  │    groundedness = 0.85  (no hallucinations?)               │
  │    completeness = 0.80  (all subtasks covered?)            │
  │    clarity      = 0.88  (well-structured?)                 │
  │  overall_score  = 0.86  → PASS  ✓                          │
  │                                                             │
  │  If score < 0.75:                                           │
  │    verdict = RETRY → return to Analyst with feedback        │
  │  If score < 0.75 AND max_iterations reached:               │
  │    verdict = ESCALATE → return best-effort answer           │
  │  ► Heartbeat: "done ✓"                                      │
  └─────────────────────────────────────────────────────────────┘
                │
                ▼
  FastAPI stores result:
    → LongTermMemory.store() → Convex vector index (if score ≥ 0.75)
    → EpisodicMemory.log() → Convex sessions table
                │
                ▼
  JSON response returned to React frontend:
  {
    session_id, query, answer, quality_score,
    verdict, subtasks[], iteration_count, llm_usage[]
  }
```

---

## Agent Reference

### Agent 1 — Planner

| Property | Value |
|---|---|
| **File** | `agents/planner.py` |
| **Model** | `meta-llama/llama-3.2-3b-instruct` |
| **Temperature** | `0.0` (fully deterministic) |
| **Max Tokens** | `512` |
| **Purpose** | Decomposes one complex query into 2–5 ordered atomic subtasks |

**How it works:**
- Calls the LLM with `PLANNER_SYSTEM_PROMPT` which instructs it to output a JSON array
- Parses the JSON defensively (strips markdown fences, uses regex fallback)
- On parse failure, retries up to 2 times; final fallback treats the whole query as one subtask
- Uses a fast, cheap model because task decomposition doesn't need deep reasoning

**Output added to state:**
```python
{ "subtasks": ["...", "..."], "current_subtask_index": 0, "llm_usage": [...], "agent_trace": [...] }
```

---

### Agent 2 — Research (ReAct Loop)

| Property | Value |
|---|---|
| **File** | `agents/research.py` |
| **Model** | `meta-llama/llama-3.1-8b-instruct` |
| **Temperature** | `0.2` |
| **Max Tokens** | `1024` |
| **Max ReAct Steps** | `5` per subtask |
| **Purpose** | Executes each subtask via a Thought → Action → Observation reasoning loop |

**How it works:**

Before the loop starts, it retrieves semantically similar past research from the Convex vector index (RAG injection) and prepends it to the task context, so the agent doesn't re-research known facts.

The ReAct loop is implemented as a **multi-turn chat conversation**:

```
Step 1: USER sends subtask + memory context
Step 2: LLM responds with:
        Thought: I need to search for X
        Action: web_search
        Action Input: latest X news 2024
Step 3: MARS parses "Action" and "Action Input" via regex
Step 4: Tool is executed → observation string returned
Step 5: MARS injects: "Observation: [result]\n\nContinue your research."
Step 6: LLM continues until it writes "Final Answer: ..."
```

If the LLM doesn't follow the format on a step, it gets a correction nudge. If max steps are reached without a Final Answer, the last assistant message is returned as a best-effort result.

**Output added to state:**
```python
{ "raw_research": ["=== Subtask 1: ... ===\n[findings]"], "current_subtask_index": idx+1 }
```

The `raw_research` list is an **append-only accumulator** — each research run adds to it, never overwrites it.

---

### Agent 3 — Analyst

| Property | Value |
|---|---|
| **File** | `agents/analyst.py` |
| **Model** | `meta-llama/llama-3.3-70b-instruct` |
| **Temperature** | `0.3` |
| **Max Tokens** | `2048` |
| **Purpose** | Synthesizes all raw research into one coherent, grounded markdown answer |

**How it works:**
- Receives the full `raw_research[]` concatenated into a single block
- Uses `ANALYST_SYSTEM_PROMPT` which strictly forbids adding facts not in the research
- On a **RETRY** pass (iteration > 0), switches to `ANALYST_RETRY_SYSTEM_PROMPT` which injects the reviewer's specific feedback
- Outputs a well-formatted markdown answer following a fixed template (Summary, Detailed Findings, Key Takeaways, Limitations)

The largest model in the pipeline is deliberately used here because synthesis quality is the most visible outcome.

---

### Agent 4 — Reviewer (LLM-as-Judge)

| Property | Value |
|---|---|
| **File** | `agents/reviewer.py` |
| **Model** | `meta-llama/llama-3.1-8b-instruct` |
| **Temperature** | `0.0` (deterministic scoring) |
| **Max Tokens** | `512` |
| **Quality Threshold** | `0.75` |
| **Purpose** | Scores the answer, decides whether to pass, retry, or escalate |

**Scoring dimensions:**
| Dimension | Description |
|---|---|
| **Relevance** | Does the answer directly address the user's original query? |
| **Groundedness** | Are all claims supported by the research? (Hallucination check) |
| **Completeness** | Are all subtasks adequately addressed? |
| **Clarity** | Is the answer well-structured and readable? |

**`overall_score` = average of 4 dimensions**

**Verdict logic:**
| Condition | Verdict |
|---|---|
| `score ≥ 0.75` | **PASS** → Send to user |
| `score < 0.75` AND iterations remain | **RETRY** → Return to Analyst with feedback |
| `score < 0.75` AND max iterations exhausted | **ESCALATE** → Best-effort answer returned with warning |

Output is parsed from a strict JSON format. Falls back to a conservative PASS at 0.5 if parsing fails (to not block the user).

---

## LangGraph Orchestration

The pipeline is wired using LangGraph's `StateGraph`. All graph topology is defined in `orchestration/graph.py`.

### Graph Topology

```
planner
  │ (always)
  ▼
research ◄─────────────────────────┐
  │                                 │
  │ route_after_research():         │
  │   idx < total? → "research" ───┘
  │   idx == total? → "analyst"
  ▼
analyst
  │ (always)
  ▼
reviewer
  │
  │ route_after_review():
  │   PASS | ESCALATE → END
  │   RETRY (iter < max)  → "analyst" (loop back)
  ▼
END
```

### Shared State (Blackboard Pattern)

Agents **never call each other directly**. All communication goes through the `AgentState` TypedDict — the pipeline's shared blackboard. LangGraph handles state merging between nodes, using `operator.add` for list fields so they accumulate correctly across multiple research passes.

---

## Tooling System

The Research Agent accesses tools via a **ToolRegistry** — an explicit, name-keyed function registry. Tools are pure functions with the signature `str → str`.

| Tool | File | Description |
|---|---|---|
| `web_search` | `tools/web_search.py` | DuckDuckGo real-time web search |
| `wiki_search` | `tools/wiki_search.py` | Wikipedia article lookup |
| `calculator` | `tools/calculator.py` | Safe math expression evaluator |
| `file_reader` | `tools/file_reader.py` | Read local files (docs, data) |

New tools can be added by registering them in `tools/registry.py:build_default_registry()` — no agent code needs to change because tool descriptions are auto-injected into the ReAct prompt.

---

## Memory System

MARS has three distinct memory layers:

### 1. In-Process Blackboard (Short-term)
The `AgentState` TypedDict shared within a single LangGraph execution. Lives only for the duration of one request.

### 2. Long-term Vector Memory (Semantic RAG)
**File:** `memory/long_term.py` | **Convex Table:** `research_memory`

- Stores synthesized answers as vector embeddings (1536-dim, `text-embedding-3-small`)
- Retrieved before each Research Agent run to inject relevant past findings
- Storage policy: only stored if `quality_score >= 0.75` (quality gate)
- TTL: 90 days (configurable via `memory_ttl_days`)
- Top-K: 3 most similar results (configurable via `memory_top_k`)

### 3. Episodic Session Log (Procedural History)
**File:** `memory/episodic.py` | **Convex Table:** `sessions`

- Stores every completed session (query, answer, score, verdict, subtasks, timestamp)
- Powers the **live-updating history sidebar** in the React UI via `useQuery`
- Cross-device persistent — not local state

---

## Convex Backend (Real-time Layer)

Convex is MARS's serverless real-time database. It has three tables/functions:

### `heartbeats` (Real-time Agent Status)
- **Mutation:** `heartbeats:update` — called by FastAPI after each graph node executes
- **Query:** `heartbeats:getStatus` — polled live by `useQuery` in the React frontend
- Shows: which agent is running, its status text, and which subtask index is active

### `sessions` (Episodic Memory)
- **Mutation:** `sessions:logSession` — called when a session completes
- **Query:** `sessions:getRecentSessions` — fetched live for the sidebar history

### `research_memory` (Vector RAG Store)
- **Mutation:** `memory:store` — stores a new research embedding
- **Action:** `memory:search` — performs vector similarity search (requires `action`, not `query`)
- **Query:** `memory:internalGet` — internal helper to fetch full doc by ID from an action

---

## Observability (Opik / Comet)

Every agent's `run()` method is wrapped with the `@trace_agent(name)` decorator from `observability/tracer.py`.

**Captured per agent call:**
- Input: query, session_id, current subtask index, iteration count
- Output: which state keys were modified, latency in ms
- Errors: exceptions are logged before re-raising

Opik is **optional** — if the API key is missing or initialization fails, the decorator becomes a no-op and the system runs without instrumentation (graceful degradation).

The frontend also shows a **per-agent LLM usage breakdown** (tokens in/out + latency) that is tracked independently at the Python level via `llm_usage[]` in the state.

---

## LLM Provider (OpenRouter)

**File:** `llm/openrouter_provider.py`

All LLM calls go through OpenRouter using the OpenAI-compatible API. This means you can swap any model (GPT-4o, Claude, Gemini, Mistral, Llama, etc.) by changing the model ID in `.env` or `config/agents.yaml` — no code changes required.

**Features:**
- Retry logic via `tenacity` (3 attempts, exponential backoff 2–15s)
- Usage tracking (`prompt_tokens`, `completion_tokens`, `total_tokens`, `latency_ms`) returned alongside every response
- Two call modes: `invoke_with_usage()` (single-turn) and `chat_with_usage()` (multi-turn, used by ReAct loop)

---

## Project Structure

```
MARS/
├── api/
│   └── main.py              # FastAPI app — routes, lifespan, singleton init
│
├── agents/
│   ├── base.py              # BaseAgent with _trace() helper
│   ├── planner.py           # Query decomposition agent
│   ├── research.py          # ReAct tool-use loop agent
│   ├── analyst.py           # Synthesis agent
│   ├── reviewer.py          # LLM-as-Judge scoring agent
│   └── prompts.py           # All system prompts centralized here
│
├── orchestration/
│   ├── graph.py             # LangGraph StateGraph definition
│   ├── state.py             # AgentState TypedDict (blackboard)
│   └── router.py            # Conditional edge routing functions
│
├── memory/
│   ├── long_term.py         # Convex vector memory (semantic RAG)
│   └── episodic.py          # Convex session log (history)
│
├── tools/
│   ├── registry.py          # ToolRegistry + build_default_registry()
│   ├── web_search.py        # DuckDuckGo search
│   ├── wiki_search.py       # Wikipedia search
│   ├── calculator.py        # Safe math evaluator
│   └── file_reader.py       # Local file reader
│
├── llm/
│   ├── provider.py          # LLMProvider abstract base class
│   └── openrouter_provider.py  # OpenRouter implementation (OpenAI-compat)
│
├── observability/
│   └── tracer.py            # @trace_agent decorator + Opik integration
│
├── config/
│   ├── settings.py          # Pydantic BaseSettings (all env vars)
│   └── agents.yaml          # Per-agent model/config reference
│
├── convex/
│   ├── schema.ts            # Convex table schemas
│   ├── heartbeats.ts        # Real-time status mutations/queries
│   ├── memory.ts            # Vector search action + store mutation
│   └── sessions.ts          # Session log mutations/queries
│
├── frontend/
│   └── src/
│       ├── App.jsx          # Full React UI (search, live status, results)
│       └── App.css          # Dark-mode design system
│
├── scripts/
│   └── smoke_test.py        # End-to-end smoke test
│
├── requirements.txt         # Python dependencies
└── .env                     # API keys (not committed)
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai) API key (free tier available)
- A [Convex](https://convex.dev) account (free tier available)
- Optional: An [Opik](https://comet.com/opik) API key for tracing

### 1. Clone & Configure

```bash
git clone https://github.com/KolipakaRamesh/MARS.git
cd MARS
```

Create your `.env` file:
```env
# Required
OPENROUTER_API_KEY=sk-or-...

# Required for real-time features and memory
CONVEX_URL=https://your-deployment.convex.cloud

# Optional: enables full trace dashboard
OPIK_API_KEY=your-key
OPIK_WORKSPACE=your-workspace
```

### 2. Python Backend

```bash
# Install all Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn api.main:app --reload --port 8000
```

### 3. Convex Backend

```bash
# Install Convex CLI (first time only)
npm install -g convex

# Initialize and deploy the Convex functions + schema
npx convex dev
```

This starts the Convex dev server, deploys the schema (tables + indexes), and watches for TypeScript changes.

### 4. React Frontend

```bash
cd frontend
npm install
npm run dev    # Dev server at http://localhost:5173
```

Or to serve via FastAPI (production mode):
```bash
cd frontend
npm run build          # builds to frontend/dist/
# FastAPI auto-serves frontend/dist/ at http://localhost:8000
```

---

## API Reference

### `POST /run` — Execute Research Pipeline

**Request:**
```json
{
  "query": "What are the latest advances in quantum computing?",
  "session_id": "mars-1234",
  "max_iterations": 3
}
```

**Response:**
```json
{
  "session_id": "mars-1234",
  "query": "What are the latest advances in quantum computing?",
  "answer": "# Answer to: ...\n## Summary\n...",
  "quality_score": 0.86,
  "verdict": "PASS",
  "subtasks": ["Find recent milestones...", "Explain error correction...", "Compare vendors..."],
  "iteration_count": 1,
  "llm_usage": [
    { "agent": "planner", "model": "llama-3.2-3b-instruct", "prompt_tokens": 120, "completion_tokens": 85, "total_tokens": 205, "latency_ms": 430 },
    { "agent": "research", "model": "llama-3.1-8b-instruct", "prompt_tokens": 1240, "completion_tokens": 420, "total_tokens": 1660, "latency_ms": 2100 },
    { "agent": "analyst",  "model": "llama-3.3-70b-instruct", "prompt_tokens": 2100, "completion_tokens": 890, "total_tokens": 2990, "latency_ms": 5200 },
    { "agent": "reviewer", "model": "llama-3.1-8b-instruct", "prompt_tokens": 310, "completion_tokens": 95, "total_tokens": 405, "latency_ms": 780 }
  ]
}
```

### `GET /health` — System Status
```json
{ "status": "ok", "system": "MARS", "graph_ready": true }
```

### `GET /sessions?n=10` — Recent Session History
```json
{
  "sessions": [
    { "session_id": "mars-1234", "query": "...", "verdict": "PASS", "quality_score": 0.86 }
  ]
}
```

---

## Configuration Reference

All settings are in `config/settings.py` and loaded from `.env`:

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required)* | Your OpenRouter API key |
| `CONVEX_URL` | `None` | Your Convex deployment URL |
| `OPIK_API_KEY` | `None` | Opik tracing key (optional) |
| `OPIK_WORKSPACE` | `None` | Opik workspace name |
| `planner_model` | `llama-3.2-3b-instruct` | Planner LLM |
| `research_model` | `llama-3.1-8b-instruct` | Research LLM |
| `analyst_model` | `llama-3.3-70b-instruct` | Analyst LLM |
| `reviewer_model` | `llama-3.1-8b-instruct` | Reviewer LLM |
| `max_iterations` | `3` | Max Analyst→Reviewer retry loops |
| `quality_threshold` | `0.75` | Min score for PASS verdict |
| `max_react_steps` | `5` | Max tool calls per subtask |
| `memory_ttl_days` | `90` | Vector memory expiry |
| `memory_top_k` | `3` | Retrieved memory snippets per query |

---

## Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **LLM Gateway** | OpenRouter | Routes to any hosted LLM model via OpenAI-compatible API |
| **LLM Models** | Meta Llama 3.x (3b, 8b, 70b) | Agent intelligence at different cost/quality tradeoffs |
| **Orchestration** | LangGraph | Stateful, graph-based multi-agent pipeline |
| **API Server** | FastAPI + Uvicorn | HTTP server exposing the research pipeline |
| **Real-time DB** | Convex | Live heartbeats, session history, vector memory |
| **Vector Search** | Convex Vector Index | 1536-dim semantic similarity for memory RAG |
| **Embeddings** | OpenAI text-embedding-3-small | Via OpenRouter for memory indexing |
| **Frontend** | React + Vite | Live dashboard with real-time Convex queries |
| **Observability** | Opik (Comet) | LLM trace capture per agent |
| **Web Search** | DuckDuckGo | Real-time factual retrieval |
| **Resiliency** | tenacity | Automatic retry with exponential backoff for all LLM calls |
| **Config** | Pydantic BaseSettings | Type-safe environment variable management |
