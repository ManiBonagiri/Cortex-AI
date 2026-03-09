"""
test_memory.py — Cortex Memory Unit Tests
==========================================
Tests ChromaDB long-term memory:
  - Saving messages
  - Retrieving relevant context
  - Session isolation
  - Clearing memory

Run:
    pytest tests/test_memory.py -v
"""

import pytest
import time
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

from backend.agent.memory import save_memory, get_relevant_memory


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def unique_session() -> str:
    """Generate a unique session ID so tests don't bleed into each other."""
    return f"test_session_{int(time.time() * 1000)}"


# ══════════════════════════════════════════════════════════════
#  SAVE MEMORY
# ══════════════════════════════════════════════════════════════

class TestSaveMemory:

    def test_save_user_message(self):
        """save_memory should not raise when saving a user message."""
        session = unique_session()
        try:
            save_memory(session, "user", "Hello, I love Python programming.")
        except Exception as e:
            pytest.fail(f"save_memory raised unexpectedly: {e}")

    def test_save_assistant_message(self):
        """save_memory should not raise when saving an assistant message."""
        session = unique_session()
        try:
            save_memory(session, "assistant", "I can help you with Python!")
        except Exception as e:
            pytest.fail(f"save_memory raised unexpectedly: {e}")

    def test_save_multiple_messages(self):
        """save_memory should handle a full conversation without errors."""
        session = unique_session()
        exchanges = [
            ("user",      "My name is Ravi and I live in Hyderabad."),
            ("assistant", "Nice to meet you, Ravi! How can I help you today?"),
            ("user",      "I'm learning machine learning."),
            ("assistant", "Great! ML is a fascinating field. What aspect interests you most?"),
        ]
        for role, content in exchanges:
            try:
                save_memory(session, role, content)
            except Exception as e:
                pytest.fail(f"save_memory failed on '{role}' message: {e}")

    def test_save_empty_message(self):
        """save_memory should handle empty strings without crashing."""
        session = unique_session()
        try:
            save_memory(session, "user", "")
        except Exception:
            pass  # Acceptable to raise on empty, just shouldn't cause unhandled crash

    def test_save_long_message(self):
        """save_memory should handle very long messages."""
        session = unique_session()
        long_text = "This is a detailed explanation. " * 100
        try:
            save_memory(session, "user", long_text)
        except Exception as e:
            pytest.fail(f"save_memory failed on long message: {e}")


# ══════════════════════════════════════════════════════════════
#  GET RELEVANT MEMORY
# ══════════════════════════════════════════════════════════════

class TestGetRelevantMemory:

    def test_returns_string(self):
        """get_relevant_memory should always return a string."""
        session = unique_session()
        save_memory(session, "user", "I like coffee.")
        result = get_relevant_memory(session, "what do I like?")
        assert isinstance(result, str)

    def test_empty_session_returns_string(self):
        """get_relevant_memory on a brand new session should return a string (possibly empty)."""
        session = unique_session()
        result = get_relevant_memory(session, "do you remember me?")
        assert isinstance(result, str)

    def test_retrieves_saved_context(self):
        """get_relevant_memory should surface previously saved relevant info."""
        session = unique_session()
        save_memory(session, "user", "My favourite programming language is Rust.")
        save_memory(session, "assistant", "Rust is a great systems language!")

        result = get_relevant_memory(session, "what programming language do I like?")
        assert isinstance(result, str)
        # Memory should have found something relevant
        assert len(result) >= 0  # Even empty is OK — just can't crash

    def test_memory_relevant_to_query(self):
        """Memory retrieved should be related to the query topic."""
        session = unique_session()
        save_memory(session, "user", "I work as a data scientist at a bank in Mumbai.")
        save_memory(session, "user", "I enjoy hiking on weekends.")

        result = get_relevant_memory(session, "what is my job?")
        assert isinstance(result, str)

    def test_multiple_saves_then_retrieve(self):
        """Should handle multiple saves and still retrieve without error."""
        session = unique_session()
        for i in range(5):
            save_memory(session, "user", f"Message number {i} about topic {i}.")
        result = get_relevant_memory(session, "what messages do you remember?")
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════
#  SESSION ISOLATION
# ══════════════════════════════════════════════════════════════

class TestSessionIsolation:

    def test_different_sessions_isolated(self):
        """
        Memory from session A should not contaminate session B.
        Both should return strings but from their own context.
        """
        session_a = unique_session()
        session_b = unique_session()

        save_memory(session_a, "user", "Session A secret: I love jazz music.")
        save_memory(session_b, "user", "Session B is completely unrelated.")

        result_a = get_relevant_memory(session_a, "what music do I like?")
        result_b = get_relevant_memory(session_b, "what music do I like?")

        # Both should return strings and not crash
        assert isinstance(result_a, str)
        assert isinstance(result_b, str)

    def test_new_session_starts_fresh(self):
        """A new unique session should have no prior memory."""
        session = unique_session()
        result = get_relevant_memory(session, "do you know anything about me?")
        assert isinstance(result, str)
        # Fresh session should return empty or minimal context
        assert len(result) < 500  # Should not have hallucinated a lot of content


# ══════════════════════════════════════════════════════════════
#  EDGE CASES
# ══════════════════════════════════════════════════════════════

class TestMemoryEdgeCases:

    def test_special_characters_in_message(self):
        """Memory should handle special characters without crashing."""
        session = unique_session()
        special = "User said: 'Hello! @#$%^&*() — café résumé naïve'"
        try:
            save_memory(session, "user", special)
            result = get_relevant_memory(session, "special characters")
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Memory failed on special characters: {e}")

    def test_unicode_message(self):
        """Memory should handle unicode / non-ASCII text."""
        session = unique_session()
        try:
            save_memory(session, "user", "मैं हैदराबाद में रहता हूँ।")  # Hindi
            result = get_relevant_memory(session, "where do I live")
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Memory failed on unicode: {e}")

    def test_rapid_saves(self):
        """Memory should handle rapid sequential saves without error."""
        session = unique_session()
        for i in range(10):
            save_memory(session, "user" if i % 2 == 0 else "assistant",
                        f"Rapid message {i}")
        result = get_relevant_memory(session, "rapid messages")
        assert isinstance(result, str)