"""
SOLARIS - SOLution ARchitecture Intelligence System
FastAPI Backend
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import RAGEngine
from tools import get_tool_definitions, execute_tool

app = FastAPI(title="SOLARIS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
rag = RAGEngine()

# In-memory session store
sessions: dict = {}

SOLARIS_SYSTEM_PROMPT = """You are SOLARIS — a senior IT Solution Architect AI with 20+ years of experience.
You help IT architects accelerate solution design by:
1. Converting natural language requirements into structured architectures
2. Generating Architecture Decision Records (ADRs)
3. Creating HLD/LLD breakdowns
4. Evaluating trade-offs (cost, scalability, security, compliance)
5. Detecting anti-patterns, vendor lock-in risks, and missing NFRs
6. Estimating TCO (Total Cost of Ownership)

You have access to the following tools:
- search_standards: Search enterprise architecture standards and reference patterns
- generate_diagram: Generate Mermaid architecture/sequence/deployment diagrams
- evaluate_tradeoffs: Evaluate architecture trade-offs across dimensions
- generate_adr: Create formal Architecture Decision Records
- estimate_tco: Estimate Total Cost of Ownership
- check_compliance: Validate against security/GDPR/compliance requirements

Always:
- Be structured and professional
- Surface risks proactively
- Reference NFRs (security, scalability, availability, GDPR)
- Suggest alternatives when patterns have downsides
- Format outputs clearly with sections and diagrams where helpful

When generating diagrams, always use Mermaid syntax wrapped in ```mermaid blocks.
When generating ADRs, use the standard format: Title, Status, Context, Decision, Consequences.
"""


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "SOLARIS"}


@app.post("/session")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"history": [], "created_at": datetime.utcnow().isoformat()}
    return {"session_id": session_id}


@app.post("/chat")
async def chat(req: ChatRequest):
    """Streaming chat endpoint with tool use"""
    session_id = req.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = {"history": [], "created_at": datetime.utcnow().isoformat()}

    session = sessions[session_id]

    # RAG: search relevant standards
    rag_context = rag.search(req.message, top_k=3)
    user_message = req.message
    if rag_context:
        user_message += f"\n\n[Relevant Enterprise Standards Retrieved]\n{rag_context}"

    session["history"].append({"role": "user", "content": user_message})

    tools = get_tool_definitions()

    async def generate():
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

        messages = session["history"].copy()
        full_response = ""
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SOLARIS_SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )

            # Stream text content
            for block in response.content:
                if block.type == "text":
                    full_response += block.text
                    # Stream chunk by chunk
                    for chunk in block.text.split("\n"):
                        yield f"data: {json.dumps({'type': 'text', 'content': chunk + chr(10)})}\n\n"

            # Check stop reason
            if response.stop_reason == "end_turn":
                break

            # Handle tool use
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        yield f"data: {json.dumps({'type': 'tool_call', 'tool': block.name, 'input': block.input})}\n\n"

                        result = execute_tool(block.name, block.input, rag)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': block.name, 'result_preview': result[:200]})}\n\n"

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        # Save final assistant message
        session["history"].append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/session/{session_id}/history")
def get_history(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    if session_id in sessions:
        sessions[session_id]["history"] = []
    return {"status": "cleared"}
