import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Plus, Trash2, MessageSquare, Clock, Globe, BarChart2, Terminal, Cloud, BookOpen, Calculator, Link, Timer, TrendingUp, DollarSign, Languages, Newspaper, Ruler } from "lucide-react";
import Message from "./Message";
import FileUpload from "./FileUpload";
import { sendMessage, clearHistory } from "../services/api";

const generateSessionId = () => crypto.randomUUID();

// Derive a short title from the first user message
const deriveTitle = (messages) => {
  const first = messages.find((m) => m.role === "user");
  if (!first) return "New Chat";
  const text = first.content.trim();
  return text.length > 42 ? text.slice(0, 42).trimEnd() + "…" : text;
};

// Format timestamp for sidebar display
const formatRelative = (isoString) => {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins  < 1)  return "Just now";
  if (mins  < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
};

const WelcomeScreen = () => (
  <div className="welcome">
    <div className="welcome__glow" />
    <div className="welcome__hex">⬡</div>
    <h2 className="welcome__title">What can I help you with?</h2>
    <p className="welcome__sub">
      Ask me anything — I can search the web, analyze CSVs, run code, and check the weather.
    </p>
    <div className="welcome__pills">
      <span className="welcome__pill">🔍 Search the web</span>
      <span className="welcome__pill">📊 Analyze a CSV</span>
      <span className="welcome__pill">🐍 Run Python code</span>
      <span className="welcome__pill">🌤️ Get weather</span>
    </div>
  </div>
);

const Chat = () => {
  const [messages,      setMessages]      = useState([]);
  const [input,         setInput]         = useState("");
  const [isLoading,     setIsLoading]     = useState(false);
  const [sessionId,     setSessionId]     = useState(() => generateSessionId());
  const [uploadedFile,  setUploadedFile]  = useState(null);   // display name
  const [uploadedPath,  setUploadedPath]  = useState(null);   // server filepath
  const [error,         setError]         = useState(null);

  // recentChats: array of { id, sessionId, title, messages, updatedAt }
  const [recentChats,    setRecentChats]    = useState([]);
  const [activeChat,     setActiveChat]     = useState(null); // id of the open chat

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // ── Save / update current chat in recentChats whenever messages change ──
  useEffect(() => {
    if (messages.length === 0) return;

    setRecentChats((prev) => {
      const exists = prev.find((c) => c.sessionId === sessionId);
      const updated = {
        id:        exists?.id || sessionId,
        sessionId,
        title:     deriveTitle(messages),
        messages:  [...messages],
        updatedAt: new Date().toISOString(),
      };
      if (exists) {
        return prev.map((c) => c.sessionId === sessionId ? updated : c);
      }
      return [updated, ...prev];
    });

    setActiveChat(sessionId);
  }, [messages, sessionId]);

  // ── New Chat ────────────────────────────────────────────────────────────
  const handleNewChat = useCallback(() => {
    const newId = generateSessionId();
    setMessages([]);
    setSessionId(newId);
    setActiveChat(null);
    setUploadedFile(null);
    setUploadedPath(null);
    setError(null);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  // ── Load a recent chat ───────────────────────────────────────────────────
  const handleLoadChat = useCallback((chat) => {
    setMessages(chat.messages);
    setSessionId(chat.sessionId);
    setActiveChat(chat.sessionId);
    setUploadedFile(null);
    setError(null);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  // ── Delete a recent chat ────────────────────────────────────────────────
  const handleDeleteChat = useCallback((e, chatSessionId) => {
    e.stopPropagation();
    setRecentChats((prev) => prev.filter((c) => c.sessionId !== chatSessionId));
    if (activeChat === chatSessionId) {
      setMessages([]);
      setSessionId(generateSessionId());
      setActiveChat(null);
    }
  }, [activeChat]);

  // ── Clear Memory ────────────────────────────────────────────────────────
  const handleClearMemory = useCallback(async () => {
    try {
      await clearHistory(sessionId);
      setMessages([]);
      setRecentChats((prev) => prev.filter((c) => c.sessionId !== sessionId));
      setActiveChat(null);
      setError(null);
    } catch {
      setError("Failed to clear memory. Is the backend running?");
    }
  }, [sessionId]);

  // ── Send Message ────────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    // If a CSV is uploaded, inject the filepath so the agent can use csv_analyzer
    const messageToSend = uploadedPath
      ? `${trimmed}\n\n[Uploaded CSV file path: ${uploadedPath}]`
      : trimmed;

    const userMessage = {
      role:      "user",
      content:   trimmed,   // show clean message in UI (no filepath clutter)
      timestamp: new Date().toISOString(),
    };

    const historyForApi = messages.map((m) => ({
      role:    m.role,
      content: m.content,
    }));

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const data = await sendMessage(messageToSend, sessionId, historyForApi);
      const assistantMessage = {
        role:       "assistant",
        content:    data.answer,
        tools_used: data.tools_used || [],
        latency_ms: data.latency_ms,
        steps:      data.steps,
        timestamp:  new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      // Clear file after it's been used
      if (uploadedPath) {
        setUploadedFile(null);
        setUploadedPath(null);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Connection failed. Make sure the backend is running on port 8000."
      );
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, messages, sessionId]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-layout">

      {/* ── SIDEBAR ── */}
      <aside className="sidebar">

        {/* Brand */}
        <div className="sidebar__brand-wrap">
          <div className="sidebar__brand">
            <div className="sidebar__logo-wrap">
              <div className="sidebar__logo-bg" />
              <span className="sidebar__logo">⬡</span>
            </div>
            <div className="sidebar__name-wrap">
              <div className="sidebar__name">Cortex</div>
              <div className="sidebar__tagline">Autonomous AI Agent</div>
            </div>
          </div>
        </div>

        {/* New Chat */}
        <div className="sidebar__actions">
          <button className="btn-new-chat" onClick={handleNewChat}>
            <Plus size={14} />
            New Chat
          </button>
        </div>

        {/* Recent Chats */}
        <div className="sidebar__section">
          <p className="sidebar__section-title">
            <Clock size={10} style={{ display: "inline", marginRight: 6 }} />
            Recent Chats
          </p>

          {recentChats.length === 0 ? (
            <div className="recent-chats__empty">
              <MessageSquare size={20} className="recent-chats__empty-icon" />
              <span>No chats yet</span>
            </div>
          ) : (
            <div className="recent-chats__list">
              {recentChats.map((chat) => (
                <div
                  key={chat.id}
                  className={`recent-chat-item ${activeChat === chat.sessionId ? "recent-chat-item--active" : ""}`}
                  onClick={() => handleLoadChat(chat)}
                >
                  <div className="recent-chat-item__icon">
                    <MessageSquare size={12} />
                  </div>
                  <div className="recent-chat-item__body">
                    <span className="recent-chat-item__title">{chat.title}</span>
                    <span className="recent-chat-item__time">
                      {formatRelative(chat.updatedAt)}
                    </span>
                  </div>
                  <button
                    className="recent-chat-item__delete"
                    onClick={(e) => handleDeleteChat(e, chat.sessionId)}
                    title="Delete chat"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bottom */}
        <div className="sidebar__bottom">
          <button className="btn-clear-memory" onClick={handleClearMemory}>
            <Trash2 size={13} />
            Clear Memory
          </button>
        </div>

      </aside>

      {/* ── MAIN ── */}
      <main className="chat-area">
        <div className="messages-container">
          {messages.length === 0 && !isLoading ? (
            <WelcomeScreen />
          ) : (
            messages.map((msg, i) => <Message key={i} message={msg} />)
          )}
          {isLoading && <Message isTyping />}
          {error && (
            <div className="error-banner">⚠ {error}</div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Bar */}
        <div className="input-bar">
          <div className="input-wrapper">
            <div className="input-left">
              <FileUpload
                uploadedFile={uploadedFile}
                onFileUploaded={(name, path) => {
                  setUploadedFile(name);
                  setUploadedPath(path);
                }}
                onClearFile={() => {
                  setUploadedFile(null);
                  setUploadedPath(null);
                }}
              />
            </div>

            <textarea
              ref={inputRef}
              className="input-field"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Cortex anything..."
              rows={1}
              disabled={isLoading}
            />

            <button
              className="send-btn"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      </main>

    </div>
  );
};

export default Chat;