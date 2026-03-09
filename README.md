# Cortex — Autonomous AI Agent

> An autonomous AI agent with reasoning, tools & long-term memory — built with LangGraph, Groq LLaMA , FastAPI, ChromaDB, and React.

---

## What is Cortex?

Cortex is a full-stack autonomous AI agent that can **think, plan, use tools, and remember** — not just chat. It uses a **ReAct (Reasoning + Acting)** loop powered by LangGraph, where the agent reasons step by step, picks the right tool, executes it, observes the result, and generates a grounded response.

Unlike a basic chatbot, Cortex actually **does things**.

---

## 14 Built-in Tools

| Tool | Description |
|------|-------------|
| 🔍 **Web Search** | Real-time internet search via Tavily API |
| 📊 **CSV Analyzer** | Upload & analyze CSV files using Pandas |
| 🐍 **Code Executor** | Write and run Python code, returns real output |
| 🌤️ **Weather** | Live weather for any city via OpenWeatherMap |
| 📖 **Wikipedia Search** | Fetch summaries from Wikipedia |
| 🧮 **Calculator** | Evaluate complex mathematical expressions |
| 🌐 **URL Reader** | Fetch and summarize content from any URL |
| 🕐 **Date & Time** | Current date, time, and timezone conversions |
| 💱 **Currency Converter** | Real-time currency exchange rates |
| 📈 **Stock Price** | Live stock prices and market data |
| 📚 **Dictionary** | Word definitions, synonyms, and usage |
| 🌍 **Translator** | Translate text between any languages |
| 📰 **News Headlines** | Latest news headlines by topic or category |
| 📏 **Unit Converter** | Convert between any units of measurement |

---

## How It Works

```
User Message
     │
     ▼
Agent reasons — "Do I need a tool?"
     │
     ├── Yes → Pick the right tool → Execute → Observe result → Reason again
     │
     └── No → Generate final answer
     │
     ▼
Grounded response + tools used + latency stats
```

The agent can chain **multiple tools** in a single response. For example:

> *"Search for top AI startups, get their stock prices, and translate the summary to Hindi"*

Cortex will automatically use `web_search` → `stock_price` → `translator`.

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Agent Brain | LangGraph (ReAct loop) |
| LLM | Groq API — LLaMA 3.3 70B Versatile |
| Long-Term Memory | ChromaDB (vector database) |
| Embeddings | all-MiniLM-L6-v2 |
| Web Search | Tavily API |
| Weather | OpenWeatherMap API |
| Code Execution | Python subprocess (sandboxed) |
| Data Analysis | Pandas |
| Config | Pydantic Settings |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React (Vite) |
| Styling | Tailwind CSS v3 |
| HTTP Client | Axios |
| Markdown | react-markdown |
| Icons | lucide-react |

### DevOps
| Layer | Technology |
|-------|-----------|
| Containerization | Docker (single container) |

---

## Project Structure

```
cortex/
├── backend/
│   ├── main.py                  # FastAPI entry point + CORS
│   ├── agent/
│   │   ├── graph.py             # LangGraph ReAct agent brain
│   │   ├── tools.py             # All 14 tools
│   │   ├── memory.py            # ChromaDB long-term memory
│   │   └── prompts.py           # System prompt
│   ├── routes/
│   │   ├── chat.py              # Chat endpoints
│   │   └── upload.py            # File upload endpoints
│   └── services/
│       └── llm.py               # Groq LLaMA client
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.jsx
│   │   │   ├── Message.jsx
│   │   │   ├── ToolBadge.jsx
│   │   │   ├── ThinkingSteps.jsx
│   │   │   └── FileUpload.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── tailwind.config.js
│   └── vite.config.js
├── uploads/
├── memory_store/
├── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/query` | Send message to Cortex agent |
| `GET` | `/api/chat/history` | Get session chat history |
| `DELETE` | `/api/chat/history` | Clear session memory |
| `GET` | `/api/chat/health` | Health check |
| `POST` | `/api/upload/csv` | Upload CSV for analysis |
| `GET` | `/api/upload/files` | List uploaded files |
| `DELETE` | `/api/upload/files` | Clear uploaded files |

Swagger docs: **http://localhost:8000/docs**

---

## Getting Started

### Option 1 — Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/ManiBonagiri/cortex.git
cd cortex

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# Build the image
docker build -t cortex .

# Run the container
docker run -p 8000:8000 --env-file .env cortex
```

### Option 2 — Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/ManiBonagiri/cortex.git
cd cortex
```

**2. Backend setup**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

**3. Frontend setup**
```bash
cd frontend
npm install
```

**4. Environment variables**
```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
TAVILY_API_KEY=your_tavily_api_key_here
WEATHER_API_KEY=your_openweathermap_key_here
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
```

**5. Run the app**
```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Free API Keys Required

| Service | Link | Free Tier |
|---------|------|-----------|
| Groq | [console.groq.com](https://console.groq.com) | Free — fast LLaMA inference |
| Tavily | [app.tavily.com](https://app.tavily.com) | 1,000 searches/month free |
| OpenWeatherMap | [openweathermap.org](https://openweathermap.org/api) | 1,000 calls/day free |

---

## Example Queries

```
"What's the weather in Hyderabad and Tokyo right now?"

"Search for the latest AI news and translate the summary to Hindi"

"Upload my sales.csv and tell me which month had the highest revenue"

"Write a Python script to generate fibonacci numbers and run it"

"What is the stock price of Apple and Microsoft today?"

"Convert 150 USD to INR and EUR"

"What time is it in New York, London and Tokyo?"

"What does 'serendipity' mean and use it in a sentence?"

"Convert 10 kilometers to miles and feet"

"Summarize the content from this URL: https://example.com"
```

---

## License

This project is for educational and portfolio purposes.

