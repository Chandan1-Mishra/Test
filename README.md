# ☀️ SOLARIS — SOLution ARchitecture Intelligence System

> A conversational AI agent for IT architects that generates solution architectures,
> diagrams, ADRs, compliance checks, and TCO estimates from plain English requirements.

---

## 📋 Table of Contents

1. [Quick Start (3 commands)](#-quick-start-3-commands)
2. [Prerequisites](#-prerequisites)
3. [Project Structure](#-project-structure)
4. [Architecture Decisions (Why X not Y)](#-architecture-decisions-why-x-not-y)
5. [How to Run — Step by Step](#-how-to-run--step-by-step)
6. [How It Works](#-how-it-works)
7. [Demo Prompts](#-demo-prompts)
8. [Troubleshooting](#-troubleshooting)

---

## ⚡ Quick Start (3 commands)

```bash
git clone https://github.com/YOUR_USERNAME/solaris.git
cd solaris
cp backend/.env.example backend/.env   # then add your ANTHROPIC_API_KEY
chmod +x start.sh && ./start.sh        # Mac/Linux
# OR: start.bat                        # Windows
```

Open **http://localhost:3000** — SOLARIS is ready.

---

## 🔧 Prerequisites

### Required Software

| Tool | Version | Install |
|------|---------|---------|
| Python | **3.10+** | https://python.org/downloads |
| Node.js | **18+** | https://nodejs.org |
| npm | **9+** | Comes with Node.js |
| Git | Any | https://git-scm.com |

> **Do NOT need:** Docker, Poetry, LangChain, LlamaIndex, Ollama, PostgreSQL, Redis

### API Keys

| Key | Where to get | Cost |
|-----|-------------|------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com | Pay-per-use (~€0.003/1K tokens) |

---

## 📁 Project Structure

```
solaris/
│
├── 📄 README.md                  ← You are here
├── 📄 .gitignore
├── 🚀 start.sh                   ← Mac/Linux one-shot launcher
├── 🚀 start.bat                  ← Windows one-shot launcher
│
├── backend/                      ← FastAPI Python backend
│   ├── main.py                   ← API server, streaming chat endpoint
│   ├── rag.py                    ← RAG engine (TF-IDF, no external DB)
│   ├── tools.py                  ← Claude tool definitions + execution
│   ├── requirements.txt          ← Python dependencies (5 packages only)
│   └── .env.example              ← Environment variable template
│
├── frontend/                     ← React + Vite frontend
│   ├── index.html                ← HTML entry point
│   ├── package.json              ← Node dependencies
│   ├── vite.config.js            ← Vite config with dev proxy
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.jsx              ← React root mount
│       └── App.jsx               ← Full UI (chat, diagrams, tools)
│
└── docs/
    └── architecture.md           ← System design notes
```

---

## 🏗️ Architecture Decisions (Why X not Y)

### ❓ Do I need LLaMA or Ollama?
**No.** LLaMA is an open-source alternative for when you don't have Claude access.
Since you have an Anthropic API key, use Claude — it's faster, smarter, and easier to call.

### ❓ Do I need LangChain?
**No.** LangChain adds significant complexity and abstraction.  
SOLARIS uses the **Anthropic SDK directly** with Claude's native **tool use** feature.
This gives you full control, better error messages, and fewer bugs.

### ❓ Which Claude model?
**`claude-sonnet-4-6`** — best balance for a hackathon:
- Fast enough for streaming (~2-3s first token)
- Smart enough for complex architecture reasoning
- Cheaper than Opus (~5x cheaper per token)
- Supports tool use natively

### ❓ Do I need chunking + embeddings?
**Yes, but lightweight.** SOLARIS includes a custom TF-IDF RAG engine (`rag.py`) that:
- Has 10 enterprise standards pre-loaded (security, GDPR, Azure, microservices, etc.)
- Searches them with cosine similarity
- Injects relevant standards into Claude's context before each call
- **No external vector DB required** (Pinecone, Weaviate, pgvector, etc.)

For production: swap `rag.py` with Azure Cognitive Search or pgvector.

### ❓ Do I need an Agentic / RAG-Agentic model?
**Yes — and SOLARIS is one.** The architecture is:

```
User Message
    │
    ▼
RAG Search (TF-IDF on enterprise standards)
    │
    ▼
Claude claude-sonnet-4-6 with 6 Tools:
  ├── search_standards    → RAG lookup
  ├── generate_diagram    → Mermaid output
  ├── evaluate_tradeoffs  → Scoring matrix
  ├── generate_adr        → ADR document
  ├── estimate_tco        → Cost table
  └── check_compliance    → GDPR/SOC2 checklist
    │
    ▼
Claude decides which tools to call (agentic loop, max 5 iterations)
    │
    ▼
Streamed response back to UI (SSE)
```

This is a **Tool-Use Agentic pattern** — the same architecture behind most production AI assistants. No LangGraph, no CrewAI needed.

### ❓ Do I need Poetry?
**No.** Poetry is a dependency manager (like pip + venv combined). It's good for production
but adds setup steps for a hackathon. SOLARIS uses plain `pip + venv` which:
- Is built into Python (no install step)
- Works everywhere
- Is faster to set up

Use Poetry only if your team already knows it or you want lock-file determinism.

---

## 🚀 How to Run — Step by Step

### Step 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/solaris.git
cd solaris
```

### Step 2 — Get your Anthropic API key

1. Go to https://console.anthropic.com
2. Click **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-...`)

### Step 3 — Set up the backend

```bash
cd backend

# Create .env from template
cp .env.example .env

# Edit .env and paste your key:
#   ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE

# Create virtual environment (built into Python, no install needed)
python3 -m venv .venv

# Activate it
source .venv/bin/activate      # Mac/Linux
# OR
.venv\Scripts\activate         # Windows

# Install dependencies (only 5 packages!)
pip install -r requirements.txt
```

### Step 4 — Start the backend

```bash
# Still inside backend/ with venv active:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Test it: http://localhost:8000/health → `{"status":"ok","service":"SOLARIS"}`

### Step 5 — Set up and start the frontend

Open a **new terminal**:

```bash
cd solaris/frontend

# Install Node dependencies
npm install

# Start dev server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in 300ms
  ➜  Local: http://localhost:3000/
```

### Step 6 — Open SOLARIS

Open **http://localhost:3000** in your browser. Done! 🎉

---

### 🪟 Windows Users — Alternative

```cmd
cd solaris\backend
copy .env.example .env
notepad .env   ← paste your key, save

cd ..
start.bat
```

---

## ⚙️ Backend Dependencies Explained

```
requirements.txt:

anthropic>=0.40.0     ← Official Claude SDK (tool use, streaming)
fastapi>=0.115.0      ← Web framework (async, fast, OpenAPI built-in)
uvicorn>=0.32.0       ← ASGI server to run FastAPI
python-dotenv>=1.0.0  ← Load .env file into os.environ
pydantic>=2.0.0       ← Data validation for request/response models
```

That's it. **No LangChain, no vector DB, no heavy ML libraries.**

---

## ⚙️ Frontend Dependencies Explained

```
package.json:

react + react-dom    ← UI library
vite                 ← Fast dev server + bundler (replaces webpack)
@vitejs/plugin-react ← Vite plugin for JSX transform
```

**No Redux, no React Router, no UI component library** — keeps the bundle tiny
and the demo snappy.

---

## 🎯 Demo Prompts

Copy-paste these during your hackathon demo:

### 1 — Full Architecture Design
```
Design a microservices architecture for an e-commerce platform expecting
10,000 daily users with peaks of 500 concurrent users during sales.
Services needed: user auth, product catalog, shopping cart, payment processing,
order management, and email notifications.
Requirements: GDPR compliant, deployed on Azure, 99.9% SLA, budget under €8k/month.
Generate the architecture diagram, identify risks, and check GDPR compliance.
```

### 2 — ADR Generation
```
We need to decide between event-driven architecture using Kafka vs
synchronous REST APIs for our order management system.
The system processes 5000 orders/day with occasional spikes to 20000.
Generate a formal Architecture Decision Record with trade-off analysis.
```

### 3 — TCO Estimation
```
Estimate the 3-year TCO for a SaaS platform on Azure with:
- 2 AKS clusters (dev + prod), 4 nodes each
- Azure SQL Business Critical
- Redis Cache Standard C2
- API Management Developer tier
- Application Gateway WAF v2
Team of 5 engineers based in Germany.
```

### 4 — Compliance Check
```
We are building a healthcare patient portal that stores medical records,
appointment history, and billing information for 50,000 EU patients.
The system uses Azure Blob Storage, Azure SQL, and a React frontend.
Check against GDPR and identify all compliance gaps.
```

---

## 🩺 Troubleshooting

### "ANTHROPIC_API_KEY not set" error
```bash
# Make sure .env exists in backend/ folder:
cat backend/.env
# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### Backend won't start — "port 8000 in use"
```bash
# Mac/Linux: kill whatever is on port 8000
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend shows "Connection error"
- Make sure backend is running: visit http://localhost:8000/health
- Check `API_BASE` in `frontend/src/App.jsx` is `http://localhost:8000`
- Check browser console for CORS errors

### "pip: command not found"
```bash
# Try python3 -m pip instead:
python3 -m pip install -r requirements.txt
```

### "npm: command not found"
- Install Node.js from https://nodejs.org (LTS version)
- Restart your terminal after installing

### Diagrams not rendering visually
Mermaid diagrams render as code in the app. To see visual diagrams:
1. Copy the `mermaid` code block
2. Paste at https://mermaid.live

---

## 🏆 Hackathon Tips

- **Demo order:** Start with prompt #1 (full architecture) — most impressive
- **Diagrams:** Show mermaid.live side-by-side for visual impact
- **Emphasise:** "No LangChain, no vector DB, no Docker — runs in 3 commands"
- **Stress the agentic loop:** Claude calls 3-4 tools per query automatically
- **GDPR angle:** Judges love compliance automation

---

## 📄 License

MIT — free to use, fork, and demo.

---

*Built with ☀️ Claude claude-sonnet-4-6 + FastAPI + React for the SOLARIS Hackathon*
