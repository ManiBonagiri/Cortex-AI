"""
Cortex — LLM Service (Groq / LLaMA)
=====================================
Initialises and returns the Groq LLaMA model for use by the agent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# ── Load .env ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def get_llm(temperature: float = 0.3) -> ChatGroq:
    """
    Return a configured ChatGroq LLM instance.
    Used by the LangGraph agent.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env file.")

    return ChatGroq(
        api_key     = GROQ_API_KEY,
        model       = DEFAULT_MODEL,
        temperature = temperature,
        max_tokens  = 2048,
    )