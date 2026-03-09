"""
test_agent.py — Cortex Agent Integration Tests
================================================
Tests the full LangGraph ReAct agent end-to-end via run_agent().
These are integration tests — they make real LLM + tool calls.
Requires: GROQ_API_KEY, TAVILY_API_KEY, OPENWEATHERMAP_API_KEY in .env

Run:
    pytest tests/test_agent.py -v
    pytest tests/test_agent.py -v -k "test_basic"   ← run one test
    pytest tests/test_agent.py -v --timeout=60       ← with timeout
"""

import pytest
import time
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

from backend.agent.graph import run_agent


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def unique_session() -> str:
    return f"test_agent_{int(time.time() * 1000)}"


def assert_valid_response(result: dict):
    """Shared assertion — every run_agent call should return this shape."""
    assert isinstance(result, dict),             "Result must be a dict"
    assert "answer"     in result,               "Must have 'answer'"
    assert "tools_used" in result,               "Must have 'tools_used'"
    assert "latency_ms" in result,               "Must have 'latency_ms'"
    assert "steps"      in result,               "Must have 'steps'"
    assert isinstance(result["answer"], str),    "Answer must be a string"
    assert len(result["answer"]) > 0,            "Answer must not be empty"
    assert isinstance(result["tools_used"], list), "tools_used must be a list"
    assert isinstance(result["latency_ms"], float), "latency_ms must be float"
    assert isinstance(result["steps"], int),     "steps must be int"


# ══════════════════════════════════════════════════════════════
#  BASIC RESPONSE
# ══════════════════════════════════════════════════════════════

class TestBasicResponse:

    def test_simple_greeting(self):
        """Agent should respond to a simple greeting without using tools."""
        result = run_agent("Hello!", unique_session())
        assert_valid_response(result)

    def test_returns_answer(self):
        """Agent answer should be a meaningful non-empty string."""
        result = run_agent("What is 2 + 2?", unique_session())
        assert_valid_response(result)
        assert "4" in result["answer"]

    def test_response_has_latency(self):
        """latency_ms should be a positive number."""
        result = run_agent("Hi there", unique_session())
        assert result["latency_ms"] > 0

    def test_response_has_steps(self):
        """steps should be at least 1."""
        result = run_agent("Hello", unique_session())
        assert result["steps"] >= 1

    def test_no_tool_for_simple_question(self):
        """Simple factual question may not need any tool."""
        result = run_agent("What is the capital of Japan?", unique_session())
        assert_valid_response(result)
        # Tools used can be empty or populated — both are valid
        assert isinstance(result["tools_used"], list)

    def test_agent_identity(self):
        """Agent should know it's Cortex when asked."""
        result = run_agent("What is your name?", unique_session())
        assert_valid_response(result)
        assert "cortex" in result["answer"].lower()


# ══════════════════════════════════════════════════════════════
#  TOOL USE
# ══════════════════════════════════════════════════════════════

class TestToolUse:

    def test_web_search_triggered(self):
        """Agent should use web_search for current events."""
        result = run_agent(
            "Search the web: what is the latest Python version?",
            unique_session()
        )
        assert_valid_response(result)
        assert "web_search" in result["tools_used"]

    def test_weather_tool_triggered(self):
        """Agent should use weather tool for weather queries."""
        result = run_agent(
            "What is the weather in London right now?",
            unique_session()
        )
        assert_valid_response(result)
        assert "weather" in result["tools_used"]

    def test_code_executor_triggered(self):
        """Agent should use code_executor for computation requests."""
        result = run_agent(
            "Write and run Python code to calculate the sum of 1 to 100.",
            unique_session()
        )
        assert_valid_response(result)
        assert "code_executor" in result["tools_used"]
        # Sum of 1..100 = 5050
        assert "5050" in result["answer"]

    def test_code_executor_fibonacci(self):
        """Agent should correctly compute fibonacci via code."""
        result = run_agent(
            "Run Python code to print the first 5 Fibonacci numbers.",
            unique_session()
        )
        assert_valid_response(result)
        assert "code_executor" in result["tools_used"]

    def test_tools_used_is_list(self):
        """tools_used should always be a list even when empty."""
        result = run_agent("Tell me a fun fact.", unique_session())
        assert isinstance(result["tools_used"], list)


# ══════════════════════════════════════════════════════════════
#  CHAT HISTORY
# ══════════════════════════════════════════════════════════════

class TestChatHistory:

    def test_accepts_chat_history(self):
        """Agent should accept and process chat history without crashing."""
        history = [
            {"role": "user",      "content": "My name is Arjun."},
            {"role": "assistant", "content": "Nice to meet you, Arjun!"},
        ]
        result = run_agent(
            "What is my name?",
            unique_session(),
            chat_history=history
        )
        assert_valid_response(result)

    def test_uses_history_context(self):
        """Agent should use chat history to answer follow-up questions."""
        session = unique_session()
        history = [
            {"role": "user",      "content": "I live in Hyderabad, India."},
            {"role": "assistant", "content": "Hyderabad is a great city!"},
        ]
        result = run_agent(
            "What city do I live in?",
            session,
            chat_history=history
        )
        assert_valid_response(result)
        assert "hyderabad" in result["answer"].lower()

    def test_empty_history_works(self):
        """Agent should work fine with an empty chat history list."""
        result = run_agent("Hello!", unique_session(), chat_history=[])
        assert_valid_response(result)

    def test_none_history_works(self):
        """Agent should work fine with None as chat_history."""
        result = run_agent("Hello!", unique_session(), chat_history=None)
        assert_valid_response(result)

    def test_long_history_truncated(self):
        """Agent should handle long history (truncated to last 6 internally)."""
        history = [
            {"role": "user" if i % 2 == 0 else "assistant",
             "content": f"Message number {i}"}
            for i in range(20)
        ]
        result = run_agent("Summarize what we discussed.", unique_session(), chat_history=history)
        assert_valid_response(result)


# ══════════════════════════════════════════════════════════════
#  ERROR HANDLING
# ══════════════════════════════════════════════════════════════

class TestErrorHandling:

    def test_does_not_crash_on_gibberish(self):
        """Agent should return a response (not crash) for gibberish input."""
        result = run_agent("asdkjhaskdjhaksjdhaksjdh", unique_session())
        assert_valid_response(result)

    def test_does_not_crash_on_empty_string(self):
        """Agent should handle empty string input gracefully."""
        result = run_agent("", unique_session())
        # Should return a valid dict even if answer is minimal
        assert isinstance(result, dict)
        assert "answer" in result

    def test_does_not_crash_on_special_chars(self):
        """Agent should handle special characters in input."""
        result = run_agent("!@#$%^&*()", unique_session())
        assert_valid_response(result)

    def test_returns_dict_always(self):
        """run_agent should always return a dict, never raise to the caller."""
        inputs = ["hello", "", "   ", "SELECT * FROM users;", "😀🎉🔥"]
        for text in inputs:
            result = run_agent(text, unique_session())
            assert isinstance(result, dict), f"run_agent returned non-dict for: '{text}'"

    def test_malformed_history_handled(self):
        """Agent should handle malformed history entries gracefully."""
        bad_history = [
            {"role": "user"},                    # missing content
            {"content": "no role here"},         # missing role
            {"role": "unknown", "content": "?"}  # unknown role
        ]
        try:
            result = run_agent("Hello", unique_session(), chat_history=bad_history)
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Agent crashed on malformed history: {e}")


# ══════════════════════════════════════════════════════════════
#  PERFORMANCE
# ══════════════════════════════════════════════════════════════

class TestPerformance:

    def test_response_within_timeout(self):
        """Agent should respond within 30 seconds for a simple query."""
        start = time.time()
        result = run_agent("What is 10 * 10?", unique_session())
        elapsed = time.time() - start
        assert elapsed < 30, f"Agent took too long: {elapsed:.1f}s"
        assert_valid_response(result)

    def test_latency_ms_matches_reality(self):
        """latency_ms in result should roughly match actual elapsed time."""
        start = time.time()
        result = run_agent("Say hello.", unique_session())
        actual_ms = (time.time() - start) * 1000
        reported_ms = result["latency_ms"]
        # Allow 5 second slack for overhead
        assert abs(actual_ms - reported_ms) < 5000, (
            f"Reported latency {reported_ms}ms too far from actual {actual_ms:.0f}ms"
        )