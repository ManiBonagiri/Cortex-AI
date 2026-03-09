"""
Cortex — Chat Routes
======================
POST /api/chat/query   — Main agent endpoint
GET  /api/chat/history — Get session chat history
DELETE /api/chat/history — Clear session memory
GET  /api/chat/health  — Health check
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.agent.graph  import run_agent
from backend.agent.memory import get_session_history, clear_session_memory

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:      str
    session_id:   Optional[str] = "default"
    chat_history: Optional[list[dict]] = []


class ChatResponse(BaseModel):
    answer:     str
    tools_used: list[str]
    latency_ms: float
    steps:      int
    session_id: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/query", response_model=ChatResponse)
async def chat_query(req: ChatRequest):
    """
    Main agent endpoint.
    Runs the Cortex ReAct agent on the user message and returns the response.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = run_agent(
            message      = req.message.strip(),
            session_id   = req.session_id,
            chat_history = req.chat_history or [],
        )

        return ChatResponse(
            answer     = result["answer"],
            tools_used = result["tools_used"],
            latency_ms = result["latency_ms"],
            steps      = result["steps"],
            session_id = req.session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/history")
async def get_history(session_id: str = "default"):
    """Get full conversation history for a session."""
    try:
        messages = get_session_history(session_id)
        return {"session_id": session_id, "messages": messages, "count": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def clear_history(session_id: str = "default"):
    """Clear all memory for a session."""
    success = clear_session_memory(session_id)
    return {"success": success, "session_id": session_id}


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "agent": "Cortex", "version": "1.0.0"}