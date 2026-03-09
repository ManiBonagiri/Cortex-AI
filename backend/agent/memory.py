"""
Cortex — Long-Term Memory
==========================
Uses ChromaDB to store and retrieve conversation history across sessions.
This gives Cortex the ability to remember users between conversations.
"""

import os
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# ── Load env ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
load_dotenv(BASE_DIR / ".env")

MEMORY_DIR = BASE_DIR / "memory_store"
MEMORY_DIR.mkdir(exist_ok=True)

# ── ChromaDB Client ───────────────────────────────────────────────────────────
_client     = chromadb.PersistentClient(path=str(MEMORY_DIR))
_embed_fn   = DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name               = "cortex_memory",
    embedding_function = _embed_fn,
)


# ── Save a message to memory ──────────────────────────────────────────────────

def save_memory(session_id: str, role: str, content: str) -> None:
    """
    Save a single message (user or assistant) to long-term memory.

    Args:
        session_id: Unique session identifier for the user.
        role:       'user' or 'assistant'
        content:    The message text.
    """
    try:
        _collection.add(
            documents  = [content],
            metadatas  = [{
                "session_id": session_id,
                "role":       role,
                "timestamp":  datetime.utcnow().isoformat(),
            }],
            ids        = [str(uuid.uuid4())],
        )
    except Exception as e:
        print(f"[Memory] Save failed: {e}")


# ── Retrieve relevant memories ────────────────────────────────────────────────

def get_relevant_memory(session_id: str, query: str, n_results: int = 5) -> str:
    """
    Retrieve the most relevant past messages for a given query.
    Used to inject context into the agent's prompt.

    Args:
        session_id: The user's session ID.
        query:      The current user message to find relevant history for.
        n_results:  How many past memories to retrieve.

    Returns:
        A formatted string of relevant past messages, or empty string if none.
    """
    try:
        total = _collection.count()
        if total == 0:
            return ""

        results = _collection.query(
            query_texts = [query],
            n_results   = min(n_results, total),
            where       = {"session_id": session_id},
        )

        if not results["documents"] or not results["documents"][0]:
            return ""

        memories = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            role      = meta.get("role", "unknown")
            timestamp = meta.get("timestamp", "")[:16].replace("T", " ")
            memories.append(f"[{timestamp}] {role.upper()}: {doc}")

        if not memories:
            return ""

        return "## Relevant Memory from Past Conversations:\n" + "\n".join(memories) + "\n"

    except Exception as e:
        print(f"[Memory] Retrieve failed: {e}")
        return ""


# ── Get full session history ──────────────────────────────────────────────────

def get_session_history(session_id: str, limit: int = 20) -> list[dict]:
    """
    Get the full conversation history for a session (for chat display).

    Args:
        session_id: The user's session ID.
        limit:      Max number of messages to return.

    Returns:
        List of dicts with role, content, timestamp.
    """
    try:
        results = _collection.get(
            where = {"session_id": session_id},
        )

        if not results["documents"]:
            return []

        messages = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            messages.append({
                "role":      meta.get("role", "unknown"),
                "content":   doc,
                "timestamp": meta.get("timestamp", ""),
            })

        # Sort by timestamp
        messages.sort(key=lambda x: x["timestamp"])
        return messages[-limit:]

    except Exception as e:
        print(f"[Memory] History fetch failed: {e}")
        return []


# ── Clear session memory ──────────────────────────────────────────────────────

def clear_session_memory(session_id: str) -> bool:
    """
    Delete all memory for a specific session.

    Args:
        session_id: The session to clear.

    Returns:
        True if successful, False otherwise.
    """
    try:
        results = _collection.get(where={"session_id": session_id})
        if results["ids"]:
            _collection.delete(ids=results["ids"])
        return True
    except Exception as e:
        print(f"[Memory] Clear failed: {e}")
        return False