"""
conftest.py — Shared pytest configuration for Cortex tests
============================================================
Automatically loaded by pytest before any test file runs.
Place this in the tests/ folder.
"""

import pytest
from dotenv import load_dotenv
from pathlib import Path

# Load .env before any test imports backend modules
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")


def pytest_configure(config):
    """Register custom markers so pytest doesn't warn about them."""
    config.addinivalue_line("markers", "slow: marks tests as slow (use -m 'not slow' to skip)")
    config.addinivalue_line("markers", "integration: marks tests that call real external APIs")


def pytest_collection_modifyitems(config, items):
    """
    Auto-mark tests in test_agent.py as 'integration' since they
    make real LLM + API calls and are slower than unit tests.
    """
    for item in items:
        if "test_agent" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "TestPerformance" in item.nodeid:
            item.add_marker(pytest.mark.slow)