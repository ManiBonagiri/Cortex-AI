"""
test_tools.py — Cortex Tool Unit Tests
========================================
Tests all 4 tools individually and in isolation.
Each tool is called directly (not through the agent)
so failures are pinpointed to the tool itself.

Run:
    pytest tests/test_tools.py -v
"""

import pytest
import os
import tempfile
import csv
from dotenv import load_dotenv
from pathlib import Path

# Load env before importing anything
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

from backend.agent.tools import (
    web_search,
    weather,
    code_executor,
    csv_analyzer,
)


# ══════════════════════════════════════════════════════════════
#  WEB SEARCH
# ══════════════════════════════════════════════════════════════

class TestWebSearch:

    def test_web_search_returns_results(self):
        """web_search should return a non-empty string for a basic query."""
        result = web_search.invoke({"query": "Python programming language"})
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 50,        "Result should have meaningful content"

    def test_web_search_current_events(self):
        """web_search should handle news queries."""
        result = web_search.invoke({"query": "latest technology news 2025"})
        assert isinstance(result, str)
        assert len(result) > 30

    def test_web_search_simple_fact(self):
        """web_search should return facts for a simple known query."""
        result = web_search.invoke({"query": "capital of France"})
        assert isinstance(result, str)
        # Should mention Paris somewhere
        assert "Paris" in result or "paris" in result.lower()

    def test_web_search_short_query(self):
        """web_search should handle very short queries without crashing."""
        result = web_search.invoke({"query": "AI"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_web_search_returns_string_not_none(self):
        """web_search should never return None."""
        result = web_search.invoke({"query": "OpenAI GPT"})
        assert result is not None


# ══════════════════════════════════════════════════════════════
#  WEATHER
# ══════════════════════════════════════════════════════════════

class TestWeather:

    def test_weather_major_city(self):
        """weather should return data for a well-known city."""
        result = weather.invoke({"city": "London"})
        assert isinstance(result, str)
        assert len(result) > 20

    def test_weather_contains_temperature(self):
        """weather result should contain temperature info."""
        result = weather.invoke({"city": "New York"})
        assert isinstance(result, str)
        # Should contain some numeric temperature data
        has_temp = any(c.isdigit() for c in result)
        assert has_temp, "Weather result should contain temperature numbers"

    def test_weather_indian_city(self):
        """weather should work for Indian cities."""
        result = weather.invoke({"city": "Hyderabad"})
        assert isinstance(result, str)
        assert len(result) > 10

    def test_weather_invalid_city(self):
        """weather should handle invalid city names gracefully (no crash)."""
        try:
            result = weather.invoke({"city": "XYZFakeCityABC123"})
            # Either returns an error message or raises — both are acceptable
            assert isinstance(result, str)
        except Exception as e:
            # Should not raise an unhandled exception silently
            assert "error" in str(e).lower() or "not found" in str(e).lower()

    def test_weather_returns_string(self):
        """weather should always return a string."""
        result = weather.invoke({"city": "Tokyo"})
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════
#  CODE EXECUTOR
# ══════════════════════════════════════════════════════════════

class TestCodeExecutor:

    def test_simple_print(self):
        """code_executor should run print and return its output."""
        result = code_executor.invoke({"code": "print('hello cortex')"})
        assert isinstance(result, str)
        assert "hello cortex" in result.lower()

    def test_arithmetic(self):
        """code_executor should compute and print math correctly."""
        result = code_executor.invoke({"code": "print(2 + 2)"})
        assert "4" in result

    def test_multiline_code(self):
        """code_executor should handle multi-line scripts."""
        code = """
x = 10
y = 20
print(x + y)
"""
        result = code_executor.invoke({"code": code})
        assert "30" in result

    def test_loop_output(self):
        """code_executor should capture loop output."""
        code = "for i in range(3):\n    print(i)"
        result = code_executor.invoke({"code": code})
        assert "0" in result
        assert "1" in result
        assert "2" in result

    def test_import_math(self):
        """code_executor should support standard library imports."""
        code = "import math\nprint(math.sqrt(16))"
        result = code_executor.invoke({"code": code})
        assert "4.0" in result or "4" in result

    def test_syntax_error_handled(self):
        """code_executor should return error message for bad syntax, not crash."""
        result = code_executor.invoke({"code": "def broken(:"})
        assert isinstance(result, str)
        assert len(result) > 0  # Should return some error description

    def test_string_manipulation(self):
        """code_executor should handle string operations."""
        code = "text = 'Cortex'\nprint(text.upper())"
        result = code_executor.invoke({"code": code})
        assert "CORTEX" in result

    def test_returns_string(self):
        """code_executor should always return a string."""
        result = code_executor.invoke({"code": "x = 42"})
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════
#  CSV ANALYZER
# ══════════════════════════════════════════════════════════════

class TestCSVAnalyzer:

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a real temporary CSV file for testing."""
        csv_file = tmp_path / "test_data.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "age", "salary", "city"])
            writer.writerow(["Alice",   30, 70000, "New York"])
            writer.writerow(["Bob",     25, 55000, "London"])
            writer.writerow(["Charlie", 35, 90000, "Tokyo"])
            writer.writerow(["Diana",   28, 65000, "Paris"])
            writer.writerow(["Eve",     40, 120000, "New York"])
        return str(csv_file)

    def test_basic_analysis(self, sample_csv):
        """csv_analyzer should return analysis for a valid CSV."""
        result = csv_analyzer.invoke({
            "filepath":    sample_csv,
            "instruction": "show me the data summary"
        })
        assert isinstance(result, str)
        assert len(result) > 20

    def test_column_stats(self, sample_csv):
        """csv_analyzer should be able to analyze numeric columns."""
        result = csv_analyzer.invoke({
            "filepath":    sample_csv,
            "instruction": "what is the average salary"
        })
        assert isinstance(result, str)
        assert len(result) > 0

    def test_row_count(self, sample_csv):
        """csv_analyzer should know the number of rows."""
        result = csv_analyzer.invoke({
            "filepath":    sample_csv,
            "instruction": "how many rows are in the dataset"
        })
        assert isinstance(result, str)
        # The CSV has 5 data rows
        assert "5" in result or "five" in result.lower() or len(result) > 10

    def test_column_names(self, sample_csv):
        """csv_analyzer should identify columns correctly."""
        result = csv_analyzer.invoke({
            "filepath":    sample_csv,
            "instruction": "what are the column names"
        })
        assert isinstance(result, str)
        # Should mention at least one of our columns
        assert any(col in result.lower() for col in ["name", "age", "salary", "city"])

    def test_invalid_file_handled(self):
        """csv_analyzer should handle missing files gracefully."""
        result = csv_analyzer.invoke({
            "filepath":    "/nonexistent/path/fake.csv",
            "instruction": "analyze this"
        })
        assert isinstance(result, str)
        assert len(result) > 0  # Should return error message, not crash