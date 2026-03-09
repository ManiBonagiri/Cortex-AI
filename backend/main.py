"""
Cortex — FastAPI Backend
==========================
Main entry point. Registers all routes and starts the server.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.chat   import router as chat_router
from backend.routes.upload import router as upload_router

# ── Load env ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup checks."""
    print("\n🧠 Cortex is starting up...")

    missing = []
    for key in ["GROQ_API_KEY", "TAVILY_API_KEY", "WEATHER_API_KEY"]:
        if not os.getenv(key):
            missing.append(key)

    if missing:
        print(f"⚠️  Missing env variables: {', '.join(missing)}")
    else:
        print("✅ All API keys loaded")

    # Ensure uploads folder exists
    uploads = BASE_DIR / "uploads"
    uploads.mkdir(exist_ok=True)
    print("✅ Uploads folder ready")

    print("🚀 Cortex is ready!\n")
    yield
    print("\n🛑 Cortex shutting down...")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Cortex API",
    description = "Autonomous AI Agent with Reasoning, Tools & Memory",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(chat_router)
app.include_router(upload_router)


@app.get("/")
async def root():
    return {
        "name":    "Cortex",
        "status":  "running",
        "version": "1.0.0",
        "docs":    "/docs",
    }