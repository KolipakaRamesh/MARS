# MARS — Multi-Agent Research System

> **Production-grade, graph-orchestrated multi-agent research pipeline**  
> LLM: OpenRouter · **Real-time Backend: Convex** · Orchestration: LangGraph · Observability: Opik

MARS answers complex research questions by deploying a team of specialized AI agents that plan, research, synthesize, and evaluate answers — with a self-correcting feedback loop and **real-time execution tracking** powered by Convex.

**Repository:** [github.com/KolipakaRamesh/MARS](https://github.com/KolipakaRamesh/MARS)

---

## High-Level Architecture

```
┌─────────────────────────────────────── REQUEST ──────────────────────────────────────────┐
│                                                                                          │
│  Web UI (React)  ◄──(useQuery)──►  CONVEX (Backend)  ◄──(Client)──►  FastAPI Server      │
│     (Frontend)        [Real-time DB / Vector Index]               (LangGraph Engine)    │
│                                                                                          │
└──────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │
┌──────────────────────────────────── LANGGRAPH PIPELINE ──────────────────────────────────┐
│                                          │                                               │
│   User Query ────────────────────────────┘                                               │
│       │                                                                                  │
│       ▼                                                                                  │
│  ┌──────────┐    JSON subtasks    ┌──────────────────────────────────────────────┐       │
│  │ PLANNER  │──────────────────►  │            RESEARCH LOOP                     │       │
│  │  Agent   │                    │                                              │       │
│  └──────────┘                    │  ┌──────────┐  (per subtask)                │       │
│                                  │  │ RESEARCH │◄─── Convex (retrieve past)   │       │
│                                  │  │  Agent   │───► web_search / wiki_search │       │
│                                  │  │  (ReAct) │     calculator / file_reader │       │
│                                  │  └──────────┘                              │       │
│                                  │       │ repeat until all subtasks done      │       │
│                                  └───────┼─────────────────────────────────────┘       │
│                                          │ raw_research[]                              │
│                                          ▼                                             │
│                                   ┌──────────┐                                         │
│                                   │ ANALYST  │◄── reviewer feedback (on RETRY)         │
│                                   │  Agent   │                                         │
│                                   └──────────┘                                         │
│                                          │ synthesized_answer                          │
│                                          ▼                                             │
│                                   ┌──────────┐                                         │
│                                   │ REVIEWER │── score < 0.75 ──► RETRY (Analyst)     │
│                                   │  Agent   │── score ≥ 0.75 ──► PASS  (→ END)       │
│                                   └──────────┘── iterations done ► ESCALATE (→ END)   │
│                                          │                                             │
└──────────────────────────────────────────┼─────────────────────────────────────────────┘
                                           │
                                   ┌───────▼───────┐
                                   │  CONVEX STORE │
                                   │ Sessions Table│
                                   │ Vector Memory │
                                   │ Heartbeats    │
                                   └───────────────┘
```

---

## Detailed Agent Breakdown

### Agent 1 — Planner
**Purpose:** Decompose the user's raw question into 2–5 ordered, atomic subtasks.  
**Model:** `meta-llama/llama-3.2-3b-instruct` (Fast/Deterministic)

### Agent 2 — Research (ReAct Loop)
**Purpose:** Execute subtasks autonomously using tools. Features a **Reason + Act** loop.  
**Model:** `meta-llama/llama-3.1-8b-instruct`  
- **Semantic Retrieval:** Before starting, it queries the **Convex Vector Index** to pull relevant past research.

### Agent 3 — Analyst
**Purpose:** Synthesize raw research findings into a clean, grounded markdown answer.  
**Model:** `meta-llama/llama-3.3-70b-instruct` (High Reasoning)

### Agent 4 — Reviewer (LLM-as-Judge)
**Purpose:** Independently scores the answer (0–1) and issues a verdict: `PASS`, `RETRY`, or `ESCALATE`.  
**Model:** `meta-llama/llama-3.1-8b-instruct`

---

## Tooling System

The **Research Agent** is equipped with a suite of specialized tools to interact with the real world. 

### Available Tools
| Tool | Description | Input |
|---|---|---|
| `web_search` | Real-time web search (DuckDuckGo) | Search query |
| `wiki_search` | Factual background & summaries (Wikipedia) | Topic name |
| `calculator` | Precise mathematical calculations | Math expression |
| `file_reader` | Read local system files/docs | File path |

### How Tools are Triggered
MARS uses a **ReAct (Reason + Act)** orchestration pattern to trigger tools dynamically. The agent does not just call a function; it reasons through a multi-step loop:

1. **Thought**: The agent analyzes the subtask and decides which information is missing.
2. **Action**: The agent identifies the specific tool required (e.g., `web_search`).
3. **Action Input**: The agent provides the precise parameters (e.g., "OpenAI Q* project details").
4. **Observation**: MARS executes the tool securely and returns the raw output to the agent.
5. **Synthesis**: The agent interprets the observation and either requests another tool or generates a **Final Answer**.

This "closed-loop" reasoning ensures that the research is grounded in verified data rather than model hallucinations.

---

## Real-time Observability

MARS features **Live execution tracking** powered by Convex:
1. **Heartbeats**: The FastAPI backend pushes "Agent Processing..." updates to Convex as the graph enters each node.
2. **UI Reactive Hooks**: The React frontend uses `useQuery` to listen to these heartbeats, displaying a pulse indicator and active subtask index in real-time.
3. **Opik Integration**: All LLM calls are traced via Comet Opik for deep debugging and performance monitoring.

---

## Memory Architecture

MARS uses a **unified Convex-backed memory system**:

1. **In-Process Blackboard**: Shared `AgentState` within the LangGraph pipeline.
2. **Long-Term Semantic Memory**: Stored in the Convex `research_memory` table with a built-in Vector Index (1536-dim). 
3. **Episodic Session Log**: Stored in the Convex `sessions` table. This powers the live-updating history sidebar in the UI.

---

## Quick Start

### 1. Backend Setup (Python)
```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env (OpenRouter & Convex URLs)
cp .env.example .env
```

### 2. Convex Setup (TypeScript)
```bash
# Initialize Convex (runs the backend and watches for changes)
npx convex dev
```

### 3. Frontend Setup (React)
```bash
cd frontend
npm install
npm run dev
```

Start the FastAPI server:
```bash
uvicorn api.main:app --reload --port 8000
```
Open `http://localhost:8000` or the Vite dev URL to start researching!

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns system status |
| `/run` | POST | Triggers the full agentic research pipeline |
| `/sessions` | GET | Returns recent history (from Convex) |
