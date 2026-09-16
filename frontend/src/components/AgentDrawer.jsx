import React, { useState, useEffect } from "react";
import { Sparkles, Send, Bot, MessageSquare, CornerDownLeft, ChevronDown, ChevronUp, Key, Settings, Check, Trash2, ExternalLink } from "lucide-react";
import { api } from "../services/api";

const PROMPT_SHORTCUTS = [
  "Why is my CPU hotter than my GPU?",
  "How to fit my model into 4GB VRAM?",
  "Explain my benchmark score",
  "How to fix thermal throttling?"
];

export function AgentDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("gpupilot_gemini_key") || "");
  const [tempKey, setTempKey] = useState("");
  const [showKeyConfig, setShowKeyConfig] = useState(false);
  const [keySavedMessage, setKeySavedMessage] = useState(false);

  const [messages, setMessages] = useState([
    {
      sender: "agent",
      text: "Hello! I am **GPUPilot AI Agent**. Ask me anything about your GPU thermals, compute bottlenecks, or batch size optimizations!",
      source: "GPUPilot Engine"
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setTempKey(apiKey);
  }, [apiKey]);

  const handleSaveKey = (e) => {
    e?.preventDefault?.();
    const clean = tempKey.trim();
    setApiKey(clean);
    if (clean) {
      localStorage.setItem("gpupilot_gemini_key", clean);
    } else {
      localStorage.removeItem("gpupilot_gemini_key");
    }
    setKeySavedMessage(true);
    setTimeout(() => {
      setKeySavedMessage(false);
      setShowKeyConfig(false);
    }, 1200);
  };

  const handleClearKey = () => {
    setApiKey("");
    setTempKey("");
    localStorage.removeItem("gpupilot_gemini_key");
    setKeySavedMessage(false);
  };

  const handleSend = async (textToSend) => {
    const q = textToSend || input;
    if (!q.trim() || isLoading) return;

    const userMsg = { sender: "user", text: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await api.askAgent(q, apiKey || null);
      setMessages((prev) => [...prev, {
        sender: "agent",
        text: res.response,
        actions: res.suggested_actions,
        source: res.source || (apiKey ? "Google Gemini (Live LLM)" : "GPUPilot Heuristic Engine")
      }]);
    } catch (err) {
      setMessages((prev) => [...prev, {
        sender: "agent",
        text: "Error connecting to AI Agent. Please verify your connection or API key.",
        source: "System Error"
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`agent-drawer-container ${isOpen ? "open" : "collapsed"}`}>
      <div className="agent-drawer-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="flex-row items-center gap-2">
          <div className="agent-avatar">
            <Bot size={18} className="text-cyan" />
          </div>
          <div>
            <div className="flex-row items-center gap-2">
              <span className="agent-title">AI Workload Explainer (Phase 9)</span>
              {apiKey ? (
                <span className="agent-mode-badge llm" title="Connected to Google Gemini Live LLM">
                  ✨ Gemini 1.5 Flash (Live LLM)
                </span>
              ) : (
                <span className="agent-mode-badge heuristic" title="Operating with built-in hardware telemetry rules">
                  ⚡ Heuristic Mode (Offline)
                </span>
              )}
            </div>
            <div className="agent-subtitle">Autonomous LLM telemetry reasoning & optimization</div>
          </div>
        </div>
        <div className="flex-row items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            className={`agent-settings-btn ${showKeyConfig ? "active" : ""}`}
            onClick={() => {
              if (!isOpen) setIsOpen(true);
              setShowKeyConfig(!showKeyConfig);
            }}
            title="Configure Gemini LLM API Key"
          >
            <Key size={15} />
            <span className="btn-label">{apiKey ? "API Key Active" : "Connect LLM"}</span>
          </button>
          <button className="agent-toggle-btn" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="agent-drawer-body">
          {/* Optional Gemini API Key Configuration Box */}
          {showKeyConfig && (
            <div className="agent-key-config-box">
              <div className="key-config-header">
                <div className="flex-row items-center gap-2">
                  <Key size={14} className="text-cyan" />
                  <strong>Google Gemini API Key (Optional)</strong>
                </div>
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noreferrer"
                  className="get-key-link"
                >
                  Get free key from Google AI Studio <ExternalLink size={12} />
                </a>
              </div>
              <p className="key-config-desc">
                Paste your Google Gemini API key below to unlock full conversational LLM reasoning like an autonomous systems engineer.
                Keys are stored only in your browser/device session. If left blank, GPUPilot operates in offline heuristic mode.
              </p>
              <form onSubmit={handleSaveKey} className="key-config-form">
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={tempKey}
                  onChange={(e) => setTempKey(e.target.value)}
                  className="key-input"
                />
                <button type="submit" className="key-save-btn">
                  {keySavedMessage ? <Check size={14} /> : "Save Key"}
                </button>
                {apiKey && (
                  <button type="button" onClick={handleClearKey} className="key-clear-btn" title="Clear key">
                    <Trash2 size={14} />
                  </button>
                )}
              </form>
            </div>
          )}

          <div className="agent-shortcuts">
            {PROMPT_SHORTCUTS.map((s, i) => (
              <button
                key={i}
                className="shortcut-chip"
                onClick={() => handleSend(s)}
                disabled={isLoading}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="agent-messages">
            {messages.map((m, i) => (
              <div key={i} className={`message-bubble ${m.sender}`}>
                {m.source && m.sender === "agent" && (
                  <div className="message-source-tag">
                    {m.source.includes("Gemini") ? "✨ " : "⚡ "}{m.source}
                  </div>
                )}
                <div className="message-content">{m.text}</div>
                {m.actions && m.actions.length > 0 && (
                  <div className="agent-actions-row">
                    {m.actions.map((act, j) => (
                      <span
                        key={j}
                        className="action-tag clickable"
                        onClick={() => handleSend(act)}
                        title="Click to ask AI about this action"
                      >
                        ⚡ {act}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message-bubble agent">
                <span className="agent-typing">
                  {apiKey ? "Querying Google Gemini with live GPU telemetry..." : "Thinking & analyzing telemetry..."}
                </span>
              </div>
            )}
          </div>

          <form
            className="agent-input-row"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <input
              type="text"
              placeholder="Ask anything about your GPU, power limit, or batch size optimizations..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !input.trim()}>
              <Send size={15} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

