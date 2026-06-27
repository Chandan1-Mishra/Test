# SOLARIS — System Architecture Documentation

## Overview

SOLARIS is a single-session conversational AI system with an agentic backend.
It uses Claude's native tool-use capability to orchestrate 6 specialist tools,
combined with a lightweight RAG engine for enterprise standard retrieval.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              React + Vite (port 3000)               │   │
│  │                                                     │   │
│  │  Sidebar         Chat Window         Tool Badges    │   │
│  │  ────────        ────────────        ────────────   │   │
│  │  Quick Prompts   SSE Stream          Live status    │   │
│  │  Capabilities    Mermaid blocks      per tool call  │   │
│  │  New Chat btn    ADR formatter                      │   │
│  └──────────────────────┬──────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP POST /chat (SSE stream)
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI (port 8000)                       │
│                                                             │
│  ┌──────────┐   ┌─────────────┐   ┌──────────────────────┐ │
│  │ /session │   │   /chat     │   │  /session/{id}/      │ │
│  │ POST     │   │   POST      │   │  history GET         │ │
│  │ Creates  │   │   Streaming │   │  Returns full        │ │
│  │ session  │   │   endpoint  │   │  conversation        │ │
│  └──────────┘   └──────┬──────┘   └──────────────────────┘ │
│                        │                                    │
│           ┌────────────┼────────────┐                       │
│           ▼            ▼            ▼                       │
│     ┌──────────┐  ┌────────┐  ┌──────────────────────────┐ │
│     │  rag.py  │  │ Claude │  │       tools.py           │ │
│     │          │  │ claude-│  │                          │ │
│     │ TF-IDF   │  │ sonnet │  │ search_standards         │ │
│     │ search   │  │ -4-6   │  │ generate_diagram         │ │
│     │ over 10  │  │        │  │ evaluate_tradeoffs        │ │
│     │ standards│  │ Tool   │  │ generate_adr             │ │
│     │          │  │ Use    │  │ estimate_tco             │ │
│     └──────────┘  │ Loop   │  │ check_compliance         │ │
│                   └────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ HTTPS
              ┌───────────────────────┐
              │   Anthropic API       │
              │   api.anthropic.com   │
              │   claude-sonnet-4-6   │
              └───────────────────────┘
```

## Agentic Loop

```
User Message
     │
     ▼
RAG: search enterprise standards (TF-IDF cosine similarity)
     │
     ▼ inject top-3 results into user message
     │
     ▼
Claude claude-sonnet-4-6 (with system prompt + 6 tools)
     │
     ├── stop_reason = "tool_use" ──► execute tools ──► append results ──► call Claude again
     │                                                                      (max 5 iterations)
     └── stop_reason = "end_turn" ──► stream final text to frontend via SSE
```

## RAG Engine Design

**Why TF-IDF instead of embeddings?**

For a hackathon with a corpus of ~10-50 documents, TF-IDF cosine similarity
performs comparably to embedding-based search, with zero setup, zero API cost,
and zero latency overhead.

**Production upgrade path:**
- Replace `rag.py` search with Azure Cognitive Search (vector index)
- Replace in-memory documents with Azure Blob Storage / Cosmos DB
- Add embedding generation via `text-embedding-3-small` from OpenAI
  or `voyage-2` from Voyage AI

## Data Flow — Single Chat Turn

```
1. POST /chat { message, session_id }
2. RAG.search(message) → top-3 standards
3. Append standards to user message
4. Add to session history
5. Call Claude API (streaming=False, tools=all_6)
6. If tool_use → execute → append → call Claude again
7. When end_turn → stream chunks via SSE to browser
8. Save final response to session history
```

## Key Design Choices

| Decision | Choice | Reason |
|----------|--------|--------|
| Framework | FastAPI | Async, fast, auto-docs at /docs |
| Streaming | SSE (not WebSocket) | Simpler, works with fetch() natively |
| State | In-memory dict | No DB needed for hackathon |
| RAG | TF-IDF | Zero setup, good enough for 10-50 docs |
| Tools | Native Anthropic tool_use | No LangChain overhead |
| Model | claude-sonnet-4-6 | Best speed/quality/cost balance |
| Frontend | React + Vite | Fast HMR, minimal config |
| Styling | CSS-in-JS (style tag) | Zero dependencies, portable |
