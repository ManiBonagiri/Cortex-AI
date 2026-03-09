"""
Cortex — Agent Tools
======================
All tools available to the Cortex ReAct agent.

Original tools (4):
  web_search, csv_analyzer, code_executor, weather

New tools (10):
  wikipedia_search, calculator, url_reader, datetime_tool,
  currency_converter, stock_price, dictionary, translator,
  news_headlines, unit_converter

Total: 14 tools
"""

import os
import re
import sys
import math
import subprocess
import tempfile
import traceback
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
from langchain_core.tools import tool
from tavily import TavilyClient

load_dotenv()

# ── API clients ───────────────────────────────────────────────────────────────
_tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))


# ══════════════════════════════════════════════════════════════
#  ORIGINAL TOOLS
# ══════════════════════════════════════════════════════════════

@tool
def web_search(query: str) -> str:
    """Search the internet for real-time information. Use for current events,
    facts, news, or anything that needs up-to-date data."""
    try:
        results = _tavily.search(query=query, max_results=5)
        if not results.get("results"):
            return "No results found."
        output = []
        for r in results["results"]:
            output.append(f"**{r.get('title', '')}**\n{r.get('content', '')}\nSource: {r.get('url', '')}")
        return "\n\n---\n\n".join(output)
    except Exception as e:
        return f"Web search error: {str(e)}"


@tool
def csv_analyzer(filepath: str, instruction: str) -> str:
    """Analyze an uploaded CSV file and extract insights based on the instruction.
    The filepath should be the path to the uploaded CSV file."""
    try:
        df = pd.read_csv(filepath)
        info = {
            "shape":        df.shape,
            "columns":      list(df.columns),
            "dtypes":       df.dtypes.astype(str).to_dict(),
            "head":         df.head(5).to_string(),
            "describe":     df.describe(include="all").to_string(),
            "null_counts":  df.isnull().sum().to_dict(),
        }
        summary = (
            f"Dataset shape: {info['shape'][0]} rows × {info['shape'][1]} columns\n"
            f"Columns: {', '.join(info['columns'])}\n\n"
            f"Data types:\n{info['dtypes']}\n\n"
            f"First 5 rows:\n{info['head']}\n\n"
            f"Statistical summary:\n{info['describe']}\n\n"
            f"Missing values:\n{info['null_counts']}\n\n"
            f"Instruction: {instruction}"
        )
        return summary
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except Exception as e:
        return f"CSV analysis error: {str(e)}"


@tool
def code_executor(code: str) -> str:
    """Write and execute Python code. Returns the actual output from running it.
    Use for calculations, data processing, algorithms, or anything computational."""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=15
        )
        os.unlink(tmp_path)
        output = result.stdout.strip()
        errors = result.stderr.strip()
        if errors and not output:
            return f"Error:\n{errors}"
        if errors:
            return f"Output:\n{output}\n\nWarnings:\n{errors}"
        return output if output else "Code ran successfully with no output."
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (15s limit)."
    except Exception as e:
        return f"Execution error: {str(e)}"


@tool
def weather(city: str) -> str:
    """Get the current weather for any city in the world."""
    try:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={api_key}&units=metric"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("cod") != 200:
            return f"Weather error: {data.get('message', 'City not found')}"
        w = data["weather"][0]
        m = data["main"]
        wind = data.get("wind", {})
        return (
            f"Weather in {data['name']}, {data['sys']['country']}:\n"
            f"Condition: {w['description'].title()}\n"
            f"Temperature: {m['temp']}°C (feels like {m['feels_like']}°C)\n"
            f"Min/Max: {m['temp_min']}°C / {m['temp_max']}°C\n"
            f"Humidity: {m['humidity']}%\n"
            f"Wind: {wind.get('speed', 'N/A')} m/s"
        )
    except Exception as e:
        return f"Weather error: {str(e)}"


# ══════════════════════════════════════════════════════════════
#  NEW TOOLS
# ══════════════════════════════════════════════════════════════

@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for detailed factual information about any topic,
    person, place, event, or concept. Returns a summary."""
    try:
        import wikipedia
        wikipedia.set_lang("en")
        results = wikipedia.search(query, results=3)
        if not results:
            return f"No Wikipedia results found for: {query}"
        # Try the top result first, fall back to next if disambiguation
        for title in results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                summary = wikipedia.summary(title, sentences=6, auto_suggest=False)
                return f"**{page.title}**\n\n{summary}\n\nSource: {page.url}"
            except wikipedia.DisambiguationError as e:
                # Try first option from disambiguation
                try:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
                    summary = wikipedia.summary(e.options[0], sentences=6, auto_suggest=False)
                    return f"**{page.title}**\n\n{summary}\n\nSource: {page.url}"
                except Exception:
                    continue
            except Exception:
                continue
        return f"Could not retrieve Wikipedia article for: {query}"
    except Exception as e:
        return f"Wikipedia error: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result.
    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, abs, round, pi, e.
    Example: '2 ** 10', 'sqrt(144)', 'sin(3.14159 / 2)'"""
    try:
        # Whitelist safe names only
        safe_names = {
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "log10": math.log10,
            "log2": math.log2, "abs": abs, "round": round,
            "pow": pow, "pi": math.pi, "e": math.e,
            "ceil": math.ceil, "floor": math.floor,
            "factorial": math.factorial, "exp": math.exp,
        }
        # Strip anything that looks dangerous
        clean = re.sub(r'[^0-9+\-*/().,\s\w]', '', expression)
        result = eval(clean, {"__builtins__": {}}, safe_names)   # nosec
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as e:
        return f"Calculator error: {str(e)}\nExpression: {expression}"


@tool
def url_reader(url: str) -> str:
    """Fetch and read the text content of any public webpage or URL.
    Useful for reading articles, documentation, or any web page content."""
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CortexBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Remove script, style, nav, footer noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive blank lines
        lines = [l for l in text.splitlines() if l.strip()]
        cleaned = "\n".join(lines[:200])  # cap at 200 lines
        return f"Content from {url}:\n\n{cleaned}"
    except requests.exceptions.HTTPError as e:
        return f"HTTP error fetching {url}: {str(e)}"
    except Exception as e:
        return f"URL reader error: {str(e)}"


@tool
def datetime_tool(timezone: str = "UTC") -> str:
    """Get the current date and time in any timezone.
    Examples of timezone: 'UTC', 'Asia/Kolkata', 'America/New_York',
    'Europe/London', 'Asia/Tokyo', 'Australia/Sydney'"""
    try:
        import pytz
        tz_name = timezone.strip() or "UTC"
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        return (
            f"Current date & time in {tz_name}:\n"
            f"Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Time: {now.strftime('%I:%M:%S %p')}\n"
            f"UTC offset: {now.strftime('%z')}\n"
            f"ISO format: {now.isoformat()}"
        )
    except Exception as e:
        # Fallback to UTC
        now = datetime.utcnow()
        return (
            f"Note: Could not find timezone '{timezone}', showing UTC.\n"
            f"Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Time: {now.strftime('%I:%M:%S %p')} UTC"
        )


@tool
def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another using real-time exchange rates.
    Examples: amount=100, from_currency='USD', to_currency='INR'
    Supports all major currencies: USD, EUR, GBP, INR, JPY, AUD, CAD, etc."""
    try:
        base = from_currency.upper().strip()
        target = to_currency.upper().strip()
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "rates" not in data:
            return f"Could not fetch rates for {base}."
        rate = data["rates"].get(target)
        if rate is None:
            return f"Currency '{target}' not found. Try a standard 3-letter code like USD, EUR, INR."
        converted = round(amount * rate, 4)
        return (
            f"💱 Currency Conversion:\n"
            f"{amount} {base} = {converted} {target}\n"
            f"Exchange rate: 1 {base} = {rate} {target}\n"
            f"Rates updated: {data.get('date', 'recently')}"
        )
    except Exception as e:
        return f"Currency converter error: {str(e)}"


@tool
def stock_price(symbol: str) -> str:
    """Get the current stock price and key info for any publicly traded company.
    Use the stock ticker symbol, e.g. 'AAPL' for Apple, 'TSLA' for Tesla,
    'GOOGL' for Google, 'RELIANCE.NS' for Reliance India."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol.upper().strip())
        info = ticker.info
        hist = ticker.history(period="2d")
        if hist.empty:
            return f"No data found for ticker symbol: {symbol}"
        current = hist["Close"].iloc[-1]
        prev    = hist["Close"].iloc[0] if len(hist) > 1 else current
        change  = current - prev
        pct     = (change / prev * 100) if prev else 0
        arrow   = "▲" if change >= 0 else "▼"
        return (
            f"📈 {info.get('longName', symbol)} ({symbol.upper()})\n"
            f"Current Price: ${current:.2f}\n"
            f"Change: {arrow} ${abs(change):.2f} ({pct:+.2f}%)\n"
            f"Market Cap: {info.get('marketCap', 'N/A')}\n"
            f"52W High: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"52W Low:  {info.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
            f"Sector: {info.get('sector', 'N/A')}"
        )
    except Exception as e:
        return f"Stock price error for '{symbol}': {str(e)}"


@tool
def dictionary(word: str) -> str:
    """Look up the definition, pronunciation, part of speech, and examples
    for any English word."""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip().lower()}"
        r = requests.get(url, timeout=10)
        if r.status_code == 404:
            return f"Word '{word}' not found in dictionary."
        data = r.json()
        entry    = data[0]
        phonetic = entry.get("phonetic", "")
        output   = [f"📖 **{entry['word']}** {phonetic}\n"]
        for meaning in entry.get("meanings", [])[:3]:
            pos  = meaning.get("partOfSpeech", "")
            defs = meaning.get("definitions", [])[:2]
            output.append(f"\n*{pos}*")
            for i, d in enumerate(defs, 1):
                output.append(f"  {i}. {d['definition']}")
                if d.get("example"):
                    output.append(f'     Example: "{d["example"]}"')
            synonyms = meaning.get("synonyms", [])[:5]
            if synonyms:
                output.append(f"  Synonyms: {', '.join(synonyms)}")
        return "\n".join(output)
    except Exception as e:
        return f"Dictionary error: {str(e)}"


@tool
def translator(text: str, target_language: str) -> str:
    """Translate any text into another language.
    Use full language names: 'Spanish', 'French', 'Hindi', 'Arabic',
    'German', 'Japanese', 'Chinese', 'Portuguese', 'Russian', 'Telugu', etc."""
    try:
        from deep_translator import GoogleTranslator
        # Map common names to language codes
        lang_map = {
            "hindi": "hi", "telugu": "te", "tamil": "ta", "kannada": "kn",
            "marathi": "mr", "bengali": "bn", "gujarati": "gu", "punjabi": "pa",
            "spanish": "es", "french": "fr", "german": "de", "italian": "it",
            "portuguese": "pt", "russian": "ru", "japanese": "ja",
            "chinese": "zh-CN", "arabic": "ar", "korean": "ko",
            "dutch": "nl", "turkish": "tr", "vietnamese": "vi",
            "thai": "th", "polish": "pl", "swedish": "sv", "english": "en",
        }
        lang_key = target_language.lower().strip()
        lang_code = lang_map.get(lang_key, lang_key)
        translated = GoogleTranslator(source="auto", target=lang_code).translate(text)
        return (
            f"🌐 Translation to {target_language.title()}:\n\n"
            f"Original: {text}\n"
            f"Translated: {translated}"
        )
    except Exception as e:
        return f"Translation error: {str(e)}"


@tool
def news_headlines(topic: str) -> str:
    """Get the latest news headlines for any topic, person, company, or event.
    Returns top 5 recent news articles with titles and summaries."""
    try:
        results = _tavily.search(
            query=f"latest news {topic}",
            max_results=5,
            search_depth="advanced",
            topic="news",
        )
        if not results.get("results"):
            return f"No news found for: {topic}"
        output = [f"📰 Latest News: {topic}\n"]
        for i, r in enumerate(results["results"], 1):
            output.append(
                f"{i}. **{r.get('title', 'No title')}**\n"
                f"   {r.get('content', '')[:200]}...\n"
                f"   Source: {r.get('url', '')}"
            )
        return "\n\n".join(output)
    except Exception as e:
        return f"News error: {str(e)}"


@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Convert values between units of measurement.
    Supported categories:
    - Length: meters, kilometers, miles, feet, inches, centimeters, yards
    - Weight: kilograms, grams, pounds, ounces, tons
    - Temperature: celsius, fahrenheit, kelvin
    - Speed: kmh, mph, ms (meters/sec)
    - Area: sqm, sqkm, sqft, acres, hectares
    - Volume: liters, ml, gallons, cups, pints"""
    try:
        f = from_unit.lower().strip()
        t = to_unit.lower().strip()
        v = float(value)

        # ── Conversion tables (all → base unit → target) ──
        length_to_m = {
            "meters": 1, "m": 1, "meter": 1,
            "kilometers": 1000, "km": 1000, "kilometer": 1000,
            "miles": 1609.344, "mile": 1609.344,
            "feet": 0.3048, "foot": 0.3048, "ft": 0.3048,
            "inches": 0.0254, "inch": 0.0254, "in": 0.0254,
            "centimeters": 0.01, "cm": 0.01, "centimeter": 0.01,
            "yards": 0.9144, "yard": 0.9144, "yd": 0.9144,
            "millimeters": 0.001, "mm": 0.001,
        }
        weight_to_kg = {
            "kilograms": 1, "kg": 1, "kilogram": 1,
            "grams": 0.001, "g": 0.001, "gram": 0.001,
            "pounds": 0.453592, "pound": 0.453592, "lb": 0.453592, "lbs": 0.453592,
            "ounces": 0.0283495, "ounce": 0.0283495, "oz": 0.0283495,
            "tons": 1000, "ton": 1000, "tonnes": 1000,
        }
        speed_to_ms = {
            "kmh": 1/3.6, "kph": 1/3.6, "km/h": 1/3.6,
            "mph": 0.44704, "mi/h": 0.44704,
            "ms": 1, "m/s": 1,
            "fps": 0.3048, "ft/s": 0.3048,
            "knots": 0.514444, "knot": 0.514444,
        }
        area_to_sqm = {
            "sqm": 1, "m2": 1, "square meters": 1,
            "sqkm": 1e6, "km2": 1e6, "square kilometers": 1e6,
            "sqft": 0.092903, "ft2": 0.092903, "square feet": 0.092903,
            "acres": 4046.86, "acre": 4046.86,
            "hectares": 10000, "hectare": 10000, "ha": 10000,
            "sqmi": 2589988, "square miles": 2589988,
        }
        volume_to_l = {
            "liters": 1, "liter": 1, "l": 1,
            "ml": 0.001, "milliliters": 0.001, "milliliter": 0.001,
            "gallons": 3.78541, "gallon": 3.78541, "gal": 3.78541,
            "cups": 0.236588, "cup": 0.236588,
            "pints": 0.473176, "pint": 0.473176,
            "quarts": 0.946353, "quart": 0.946353,
            "fl oz": 0.0295735, "fluid ounces": 0.0295735,
        }

        # ── Temperature (special case) ──
        temp_units = {"celsius", "c", "fahrenheit", "f", "kelvin", "k"}
        if f in temp_units or t in temp_units:
            def to_celsius(val, unit):
                if unit in ("celsius", "c"):   return val
                if unit in ("fahrenheit", "f"): return (val - 32) * 5/9
                if unit in ("kelvin", "k"):     return val - 273.15
                raise ValueError(f"Unknown temp unit: {unit}")
            def from_celsius(val, unit):
                if unit in ("celsius", "c"):    return val
                if unit in ("fahrenheit", "f"): return val * 9/5 + 32
                if unit in ("kelvin", "k"):     return val + 273.15
                raise ValueError(f"Unknown temp unit: {unit}")
            result = from_celsius(to_celsius(v, f), t)
            return f"🌡️ {v} {from_unit} = {round(result, 4)} {to_unit}"

        # ── Generic table lookup ──
        for table, label in [
            (length_to_m,   "Length"),
            (weight_to_kg,  "Weight"),
            (speed_to_ms,   "Speed"),
            (area_to_sqm,   "Area"),
            (volume_to_l,   "Volume"),
        ]:
            if f in table and t in table:
                in_base = v * table[f]
                result  = in_base / table[t]
                return f"📐 {label}: {v} {from_unit} = {round(result, 6)} {to_unit}"

        return (
            f"Could not convert '{from_unit}' to '{to_unit}'.\n"
            f"Supported: length, weight, temperature, speed, area, volume units."
        )
    except Exception as e:
        return f"Unit converter error: {str(e)}"


# ══════════════════════════════════════════════════════════════
#  TOOL REGISTRY
# ══════════════════════════════════════════════════════════════

ALL_TOOLS = [
    # Original 4
    web_search,
    csv_analyzer,
    code_executor,
    weather,
    wikipedia_search,
    calculator,
    url_reader,
    datetime_tool,
    currency_converter,
    stock_price,
    dictionary,
    translator,
    news_headlines,
    unit_converter,
]