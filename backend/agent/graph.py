"""
Cortex — Agent Brain (LangGraph)
==================================
Implements a ReAct (Reasoning + Acting) agent using LangGraph.
The agent reasons step by step, picks tools, executes them,
observes results, and generates a final grounded response.

Flow:
  User Input → [Inject Memory] → Agent Node → Tool Node (if needed) → Agent Node → Response
"""

import re
import time
import logging
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from pathlib import Path

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from backend.services.llm  import get_llm
from backend.agent.tools   import ALL_TOOLS
from backend.agent.prompts import CORTEX_SYSTEM_PROMPT
from backend.agent.memory  import save_memory, get_relevant_memory

logger = logging.getLogger(__name__)

# ── Load env ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
load_dotenv(BASE_DIR / ".env")

MAX_STEPS = 8


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_rate_limit(error: Exception) -> bool:
    return "429" in str(error) or "rate_limit_exceeded" in str(error)


def _parse_retry_time(error: Exception) -> str:
    match = re.search(r"try again in ([\w.]+s)", str(error))
    return match.group(1) if match else "a few minutes"


def _rate_limit_message(error: Exception) -> str:
    retry_in = _parse_retry_time(error)
    return (
        f"⚠️ **Groq API rate limit reached.**\n\n"
        f"You've used up your free daily token quota (100k tokens/day). "
        f"Please wait **{retry_in}** and try again.\n\n"
        f"To remove this limit, upgrade to Groq Dev Tier at "
        f"[console.groq.com/settings/billing](https://console.groq.com/settings/billing)."
    )


# ── Agent State ───────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages:   Annotated[list[BaseMessage], add_messages]
    session_id: str
    tools_used: list[str]
    step_count: int


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_agent():
    llm       = get_llm(temperature=0)
    llm_tools = llm.bind_tools(ALL_TOOLS)
    tool_node = ToolNode(ALL_TOOLS)

    def agent_node(state: AgentState) -> AgentState:
        messages   = state["messages"]
        session_id = state.get("session_id", "default")
        step_count = state.get("step_count", 0)

        last_human = next(
            (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
            ""
        )

        memory_context = get_relevant_memory(session_id, last_human)
        system_content = CORTEX_SYSTEM_PROMPT
        if memory_context:
            system_content += f"\n\n{memory_context}"

        full_messages = [SystemMessage(content=system_content)] + messages

        MAX_RETRIES = 3
        last_error  = None

        for attempt in range(MAX_RETRIES):
            try:
                response = llm_tools.invoke(full_messages)
                return {
                    "messages":   [response],
                    "tools_used": state.get("tools_used", []),
                    "step_count": step_count + 1,
                }

            except Exception as e:
                last_error = e
                error_str  = str(e)

                # 429 — no point retrying, bubble up immediately
                if _is_rate_limit(e):
                    logger.warning("Groq rate limit hit — propagating.")
                    raise

                # tool_use_failed — simplify and retry
                if "tool_use_failed" in error_str or "failed_generation" in error_str:
                    logger.warning(f"tool_use_failed attempt {attempt + 1}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES - 1:
                        correction = SystemMessage(
                            content=(
                                "Your last tool call was malformed. "
                                "Use ONE tool with a SHORT query under 8 words. "
                                "No commas, quotes, or special characters. Try again."
                            )
                        )
                        full_messages = full_messages + [correction]
                    continue

                # anything else — raise immediately
                logger.error(f"Agent node error (non-retryable): {e}")
                raise

        # all retries exhausted
        logger.error(f"All retries failed. Last: {last_error}")
        fallback = AIMessage(
            content=(
                "I had trouble with that request. "
                "Try asking one focused question at a time."
            )
        )
        return {
            "messages":   [fallback],
            "tools_used": state.get("tools_used", []),
            "step_count": step_count + 1,
        }

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if state.get("step_count", 0) >= MAX_STEPS:
            logger.warning(f"MAX_STEPS reached. Forcing END.")
            return END
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    def track_tools(state: AgentState) -> AgentState:
        tools_used = list(state.get("tools_used", []))
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            for tc in last.tool_calls:
                name = tc.get("name", "")
                if name and name not in tools_used:
                    tools_used.append(name)
        return {"tools_used": tools_used}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("track", track_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "track", END: END})
    graph.add_edge("track", "tools")
    graph.add_edge("tools", "agent")

    return graph.compile()


# ── Singleton ─────────────────────────────────────────────────────────────────
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


# ── Main run function ─────────────────────────────────────────────────────────

def run_agent(message: str, session_id: str, chat_history: list[dict] = None) -> dict:
    start_time = time.time()
    agent      = get_agent()

    messages = []
    if chat_history:
        for msg in chat_history[-6:]:
            role    = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=message))
    save_memory(session_id, "user", message)

    try:
        result = agent.invoke({
            "messages":   messages,
            "session_id": session_id,
            "tools_used": [],
            "step_count": 0,
        })

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)

        if _is_rate_limit(e):
            logger.warning(f"Rate limit in run_agent: {e}")
            return {
                "answer":     _rate_limit_message(e),
                "tools_used": [],
                "latency_ms": latency_ms,
                "steps":      0,
            }

        logger.error(f"Agent invocation failed: {e}")
        return {
            "answer":     "Sorry, something went wrong. Please try again in a moment.",
            "tools_used": [],
            "latency_ms": latency_ms,
            "steps":      0,
        }

    final_message = result["messages"][-1]
    answer        = final_message.content if hasattr(final_message, "content") else str(final_message)
    tools_used    = result.get("tools_used", [])
    steps         = len(result["messages"])
    latency_ms    = round((time.time() - start_time) * 1000, 2)

    save_memory(session_id, "assistant", answer)

    return {
        "answer":     answer,
        "tools_used": tools_used,
        "latency_ms": latency_ms,
        "steps":      steps,
    }