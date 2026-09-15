import React, { useState } from "react";
import { Sparkles, Send, Bot, MessageSquare, CornerDownLeft, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "../services/api";

const PROMPT_SHORTCUTS = [
  "Why is my CPU hotter than my GPU?",
  "How to fit my model into 4GB VRAM?",
  "Explain my benchmark score",
  "How to fix thermal throttling?"
];

export function AgentDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: "agent",
      text: "Hello! I am **GPUPilot AI Agent**. Ask me anything about your GPU thermals, compute bottlenecks, or batch size optimizations!"
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (textToSend) => {
    const q = textToSend || input;
    if (!q.trim() || isLoading) return;

    const userMsg = { sender: "user", text: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await api.askAgent(q);
      setMessages((prev) => [...prev, {
        sender: "agent",
        text: res.response,
        actions: res.suggested_actions
      }]);
    } catch (err) {
      setMessages((prev) => [...prev, {
        sender: "agent",
        text: "Error connecting to AI Agent. Please ensure the backend is running."
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
            <div className="agent-title">AI Workload Explainer (Phase 9)</div>
            <div className="agent-subtitle">Contextual hardware & bottleneck guidance</div>
          </div>
        </div>
        <button className="agent-toggle-btn">
          {isOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
        </button>
      </div>

      {isOpen && (
        <div className="agent-drawer-body">
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
                <div className="message-content">{m.text}</div>
                {m.actions && m.actions.length > 0 && (
                  <div className="agent-actions-row">
                    {m.actions.map((act, j) => (
                      <span key={j} className="action-tag">⚡ {act}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message-bubble agent">
                <span className="agent-typing">Thinking & analyzing telemetry...</span>
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
              placeholder="Ask about your GPU, thermal headroom, or CUDA bottlenecks..."
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
