"""
test_all_tools_quick.py
========================
Quick sanity check for all 14 Cortex tools.
Run from D:\\cortex:
    python test_all_tools_quick.py
"""

import sys
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

# ── Color helpers ─────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(name):  print(f"  {GREEN}✓ PASS{RESET}  {name}")
def fail(name, err): print(f"  {RED}✗ FAIL{RESET}  {name}\n         {YELLOW}{err}{RESET}")

# ── Import all tools ──────────────────────────────────────────
print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════╗{RESET}")
print(f"{BOLD}{CYAN}║     CORTEX — Tool Check (14 tools)       ║{RESET}")
print(f"{BOLD}{CYAN}╚══════════════════════════════════════════╝{RESET}\n")

try:
    from backend.agent.tools import (
        web_search, csv_analyzer, code_executor, weather,
        wikipedia_search, calculator, url_reader, datetime_tool,
        currency_converter, stock_price, dictionary, translator,
        news_headlines, unit_converter,
    )
    print(f"{GREEN}✓ All tools imported successfully{RESET}\n")
except ImportError as e:
    print(f"{RED}✗ Import failed: {e}{RESET}")
    sys.exit(1)

results = {"pass": 0, "fail": 0}

def run_test(name, fn):
    try:
        start  = time.time()
        result = fn()
        elapsed = round((time.time() - start) * 1000)
        assert isinstance(result, str) and len(result) > 5, "Empty or non-string result"
        ok(f"{name:<30} ({elapsed}ms)")
        results["pass"] += 1
    except Exception as e:
        fail(name, str(e)[:120])
        results["fail"] += 1

# ════════════════════════════════════════════
print(f"{BOLD}── Original Tools ──────────────────────────{RESET}")
# ════════════════════════════════════════════

run_test("web_search",
    lambda: web_search.invoke({"query": "Python programming"}))

run_test("weather",
    lambda: weather.invoke({"city": "London"}))

run_test("code_executor",
    lambda: code_executor.invoke({"code": "print('hello cortex')"}))

# CSV analyzer needs a real temp file
import tempfile, os, csv as _csv
tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
writer = _csv.writer(tmp)
writer.writerow(["name", "score"])
writer.writerows([["Alice", 90], ["Bob", 85], ["Charlie", 92]])
tmp.close()
run_test("csv_analyzer",
    lambda: csv_analyzer.invoke({"filepath": tmp.name, "instruction": "show summary"}))
os.unlink(tmp.name)

# ════════════════════════════════════════════
print(f"\n{BOLD}── New Tools ───────────────────────────────{RESET}")
# ════════════════════════════════════════════

run_test("wikipedia_search",
    lambda: wikipedia_search.invoke({"query": "Albert Einstein"}))

run_test("calculator",
    lambda: calculator.invoke({"expression": "sqrt(144) + 2 ** 8"}))

run_test("url_reader",
    lambda: url_reader.invoke({"url": "https://example.com"}))

run_test("datetime_tool (UTC)",
    lambda: datetime_tool.invoke({"timezone": "UTC"}))

run_test("datetime_tool (IST)",
    lambda: datetime_tool.invoke({"timezone": "Asia/Kolkata"}))

run_test("currency_converter",
    lambda: currency_converter.invoke({"amount": 100.0, "from_currency": "USD", "to_currency": "INR"}))

run_test("stock_price",
    lambda: stock_price.invoke({"symbol": "AAPL"}))

run_test("dictionary",
    lambda: dictionary.invoke({"word": "ephemeral"}))

run_test("translator",
    lambda: translator.invoke({"text": "Hello, how are you?", "target_language": "Hindi"}))

run_test("news_headlines",
    lambda: news_headlines.invoke({"topic": "artificial intelligence"}))

run_test("unit_converter (km→miles)",
    lambda: unit_converter.invoke({"value": 10.0, "from_unit": "kilometers", "to_unit": "miles"}))

run_test("unit_converter (°C→°F)",
    lambda: unit_converter.invoke({"value": 100.0, "from_unit": "celsius", "to_unit": "fahrenheit"}))

run_test("unit_converter (kg→pounds)",
    lambda: unit_converter.invoke({"value": 70.0, "from_unit": "kilograms", "to_unit": "pounds"}))

# ════════════════════════════════════════════
print(f"\n{BOLD}{'═'*44}{RESET}")
total = results['pass'] + results['fail']
color = GREEN if results['fail'] == 0 else RED
print(f"{color}{BOLD}  Result: {results['pass']}/{total} tools passed{RESET}")

if results['fail'] > 0:
    print(f"\n{YELLOW}  Fix tips:{RESET}")
    print(f"  • FAIL on stock_price   → pip install yfinance")
    print(f"  • FAIL on translator    → pip install deep-translator")
    print(f"  • FAIL on wikipedia     → pip install wikipedia")
    print(f"  • FAIL on url_reader    → pip install beautifulsoup4")
    print(f"  • FAIL on datetime_tool → pip install pytz")
    print(f"  • FAIL on currency/news → check internet connection")
    print(f"  • FAIL on weather       → check OPENWEATHERMAP_API_KEY in .env")
    print(f"  • FAIL on web_search    → check TAVILY_API_KEY in .env")
print()