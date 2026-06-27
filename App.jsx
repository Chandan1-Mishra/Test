import { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";

// Mermaid diagram renderer component
function MermaidDiagram({ code }) {
  const ref = useRef(null);
  const [rendered, setRendered] = useState("");
  const [error, setError] = useState(false);

  useEffect(() => {
    // Show raw mermaid code with syntax highlighting since we can't load mermaid
    setRendered(code);
  }, [code]);

  return (
    <div className="mermaid-container">
      <div className="mermaid-header">
        <span>📊 Architecture Diagram (Mermaid)</span>
        <button onClick={() => navigator.clipboard.writeText(code)} className="copy-btn">Copy</button>
      </div>
      <pre className="mermaid-code">{code}</pre>
      <div className="mermaid-hint">
        💡 Paste into <a href="https://mermaid.live" target="_blank" rel="noreferrer">mermaid.live</a> to render
      </div>
    </div>
  );
}

// Parse message content for special blocks
function MessageContent({ content }) {
  const parts = [];
  const regex = /```mermaid\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "mermaid", content: match[1] });
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < content.length) {
    parts.push({ type: "text", content: content.slice(lastIndex) });
  }

  return (
    <div className="message-content">
      {parts.map((part, i) =>
        part.type === "mermaid" ? (
          <MermaidDiagram key={i} code={part.content} />
        ) : (
          <FormattedText key={i} text={part.content} />
        )
      )}
    </div>
  );
}

function FormattedText({ text }) {
  // Convert markdown-ish formatting
  const lines = text.split("\n");
  return (
    <div>
      {lines.map((line, i) => {
        if (line.startsWith("# ")) return <h2 key={i} className="md-h1">{line.slice(2)}</h2>;
        if (line.startsWith("## ")) return <h3 key={i} className="md-h2">{line.slice(3)}</h3>;
        if (line.startsWith("### ")) return <h4 key={i} className="md-h3">{line.slice(4)}</h4>;
        if (line.startsWith("| ")) return <TableRow key={i} line={line} />;
        if (line.startsWith("- ") || line.startsWith("* ")) return <li key={i} className="md-li">{formatInline(line.slice(2))}</li>;
        if (line.match(/^\d+\. /)) return <li key={i} className="md-li md-ol">{formatInline(line.replace(/^\d+\. /, ""))}</li>;
        if (line.startsWith("**") && line.endsWith("**")) return <p key={i} className="md-bold-p">{formatInline(line)}</p>;
        if (line === "---" || line === "---") return <hr key={i} className="md-hr" />;
        if (line.trim() === "") return <br key={i} />;
        return <p key={i} className="md-p">{formatInline(line)}</p>;
      })}
    </div>
  );
}

function TableRow({ line }) {
  if (line.match(/^\|[-| ]+\|$/)) return null;
  const cells = line.split("|").filter((_, i, arr) => i > 0 && i < arr.length - 1);
  return (
    <tr>{cells.map((c, i) => <td key={i} className="md-td">{formatInline(c.trim())}</td>)}</tr>
  );
}

function formatInline(text) {
  // Bold **text**
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|⚠️|✅|❌|🔴|💡|☁️|📊|🔐)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`")) return <code key={i} className="inline-code">{p.slice(1, -1)}</code>;
    return p;
  });
}

// Tool call indicator
function ToolCallBadge({ tool }) {
  const icons = {
    search_standards: "🔍",
    generate_diagram: "📊",
    evaluate_tradeoffs: "⚖️",
    generate_adr: "📋",
    estimate_tco: "💰",
    check_compliance: "✅",
  };
  const labels = {
    search_standards: "Searching standards...",
    generate_diagram: "Generating diagram...",
    evaluate_tradeoffs: "Evaluating trade-offs...",
    generate_adr: "Creating ADR...",
    estimate_tco: "Estimating TCO...",
    check_compliance: "Checking compliance...",
  };
  return (
    <div className="tool-badge">
      <span className="tool-icon">{icons[tool] || "🔧"}</span>
      <span>{labels[tool] || `Using ${tool}...`}</span>
      <span className="tool-spinner">⟳</span>
    </div>
  );
}

const QUICK_PROMPTS = [
  { label: "🏗️ Design Microservices", prompt: "Design a microservices architecture for an e-commerce platform with 10k daily users. Include auth, product catalog, orders, payments, and notifications services. We need GDPR compliance and Azure deployment." },
  { label: "🔐 Secure API Architecture", prompt: "Design a secure API architecture for a healthcare platform handling patient data. We need HIPAA compliance, OAuth 2.0, rate limiting, and must avoid vendor lock-in." },
  { label: "📊 Data Platform Design", prompt: "Design a modern data platform for a retail company. We need real-time analytics, ML capabilities, GDPR compliance, and cost under €50k/year. 5TB data per month." },
  { label: "⚖️ Compare Cloud Options", prompt: "Compare Azure vs AWS for hosting a B2B SaaS platform with 500 enterprise customers in Europe. Evaluate cost, compliance, scalability, and vendor lock-in risks." },
  { label: "📋 Generate ADR", prompt: "Generate an Architecture Decision Record for choosing between a monolith vs microservices for a startup with 3 developers building a project management tool." },
  { label: "💰 TCO Estimate", prompt: "Estimate the TCO for a 3-tier web application on Azure: 2 AKS node pools, Azure SQL, Redis Cache, API Management, and Application Gateway. Team of 4 engineers for 3 years." },
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [activeTools, setActiveTools] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const userText = text || input.trim();
    if (!userText || loading) return;

    setInput("");
    setLoading(true);
    setActiveTools([]);

    const userMsg = { role: "user", content: userText, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);

    const assistantMsg = { role: "assistant", content: "", id: Date.now() + 1, streaming: true };
    setMessages(prev => [...prev, assistantMsg]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, session_id: sessionId }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "session_id") {
              setSessionId(data.session_id);
            } else if (data.type === "text") {
              setMessages(prev => prev.map(m =>
                m.id === assistantMsg.id
                  ? { ...m, content: m.content + data.content }
                  : m
              ));
            } else if (data.type === "tool_call") {
              setActiveTools(prev => [...prev.filter(t => t !== data.tool), data.tool]);
            } else if (data.type === "tool_result") {
              setActiveTools(prev => prev.filter(t => t !== data.tool));
            } else if (data.type === "done") {
              setMessages(prev => prev.map(m =>
                m.id === assistantMsg.id ? { ...m, streaming: false } : m
              ));
              setActiveTools([]);
            }
          } catch {}
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === assistantMsg.id
          ? { ...m, content: `⚠️ Connection error: ${err.message}\n\nMake sure the SOLARIS backend is running on port 8000.`, streaming: false }
          : m
      ));
    } finally {
      setLoading(false);
      setActiveTools([]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearSession = () => {
    setMessages([]);
    setSessionId(null);
    setActiveTools([]);
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">☀️</span>
            <div>
              <div className="logo-title">SOLARIS</div>
              <div className="logo-sub">Architecture Intelligence</div>
            </div>
          </div>
          <button className="toggle-btn" onClick={() => setSidebarOpen(f => !f)}>
            {sidebarOpen ? "◀" : "▶"}
          </button>
        </div>

        {sidebarOpen && (
          <>
            <div className="sidebar-section">
              <div className="sidebar-label">Quick Start</div>
              {QUICK_PROMPTS.map((p, i) => (
                <button key={i} className="quick-btn" onClick={() => sendMessage(p.prompt)}>
                  {p.label}
                </button>
              ))}
            </div>

            <div className="sidebar-section">
              <div className="sidebar-label">Capabilities</div>
              <div className="capability-list">
                {[
                  ["📊", "Architecture Diagrams", "Mermaid HLD/LLD/Sequence"],
                  ["📋", "ADR Generation", "Architecture Decision Records"],
                  ["⚖️", "Trade-off Analysis", "Cost vs Scalability vs Security"],
                  ["✅", "Compliance Check", "GDPR, SOC2, ISO 27001"],
                  ["💰", "TCO Estimation", "1/3/5 year cost projections"],
                  ["🔍", "Standards Search", "Enterprise reference patterns"],
                ].map(([icon, title, sub], i) => (
                  <div key={i} className="capability-item">
                    <span className="cap-icon">{icon}</span>
                    <div>
                      <div className="cap-title">{title}</div>
                      <div className="cap-sub">{sub}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="sidebar-footer">
              <button className="new-chat-btn" onClick={clearSession}>+ New Architecture</button>
              <div className="model-badge">claude-sonnet-4-6 + RAG</div>
            </div>
          </>
        )}
      </aside>

      {/* Main Chat */}
      <main className="main">
        <div className="chat-header">
          <div className="header-left">
            {!sidebarOpen && <button className="toggle-btn-main" onClick={() => setSidebarOpen(true)}>☰</button>}
            <h1 className="header-title">SOLARIS Agent</h1>
            {sessionId && <span className="session-tag">Session: {sessionId.slice(0, 8)}</span>}
          </div>
          <div className="header-right">
            {activeTools.length > 0 && activeTools.map(t => <ToolCallBadge key={t} tool={t} />)}
          </div>
        </div>

        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-icon">☀️</div>
              <h2 className="welcome-title">Welcome to SOLARIS</h2>
              <p className="welcome-sub">
                Your AI Solution Architecture Intelligence System.<br />
                Describe your project requirements and I'll generate architectures,<br />
                diagrams, ADRs, compliance checks, and cost estimates.
              </p>
              <div className="welcome-grid">
                {QUICK_PROMPTS.slice(0, 3).map((p, i) => (
                  <button key={i} className="welcome-card" onClick={() => sendMessage(p.prompt)}>
                    <span className="wc-label">{p.label}</span>
                    <span className="wc-desc">{p.prompt.slice(0, 80)}...</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="msg-avatar">
                {msg.role === "user" ? "👤" : "☀️"}
              </div>
              <div className="msg-body">
                <div className="msg-role">{msg.role === "user" ? "You" : "SOLARIS"}</div>
                {msg.role === "assistant" ? (
                  <MessageContent content={msg.content} />
                ) : (
                  <p className="user-text">{msg.content}</p>
                )}
                {msg.streaming && <span className="cursor-blink">▋</span>}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div className="input-box">
            <textarea
              ref={textareaRef}
              className="input-textarea"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your architecture requirements... (Shift+Enter for new line)"
              rows={3}
              disabled={loading}
            />
            <button
              className={`send-btn ${loading ? "loading" : ""}`}
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
            >
              {loading ? "⟳" : "↑"}
            </button>
          </div>
          <div className="input-hint">
            SOLARIS uses Claude claude-sonnet-4-6 + Enterprise RAG • Press Enter to send
          </div>
        </div>
      </main>

      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body { 
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #0f1117;
          color: #e2e8f0;
          height: 100vh;
          overflow: hidden;
        }
        
        .app { display: flex; height: 100vh; }
        
        /* Sidebar */
        .sidebar {
          width: 280px;
          background: #161b27;
          border-right: 1px solid #1e2d40;
          display: flex;
          flex-direction: column;
          transition: width 0.2s;
          overflow: hidden;
          flex-shrink: 0;
        }
        .sidebar.closed { width: 48px; }
        
        .sidebar-header {
          padding: 16px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid #1e2d40;
        }
        
        .logo { display: flex; align-items: center; gap: 10px; }
        .logo-icon { font-size: 24px; }
        .logo-title { font-size: 16px; font-weight: 700; color: #f59e0b; letter-spacing: 1px; }
        .logo-sub { font-size: 10px; color: #64748b; }
        
        .toggle-btn, .toggle-btn-main {
          background: #1e2d40; border: none; color: #94a3b8;
          width: 28px; height: 28px; border-radius: 6px; cursor: pointer;
          display: flex; align-items: center; justify-content: center; font-size: 11px;
        }
        .toggle-btn:hover, .toggle-btn-main:hover { background: #263347; color: #e2e8f0; }
        
        .sidebar-section { padding: 12px; border-bottom: 1px solid #1e2d40; }
        .sidebar-label { font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        
        .quick-btn {
          width: 100%; text-align: left; padding: 8px 10px;
          background: transparent; border: 1px solid transparent;
          color: #94a3b8; font-size: 12px; border-radius: 6px; cursor: pointer;
          display: block; margin-bottom: 2px; transition: all 0.15s;
        }
        .quick-btn:hover { background: #1e2d40; border-color: #263347; color: #e2e8f0; }
        
        .capability-list { display: flex; flex-direction: column; gap: 6px; }
        .capability-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
        .cap-icon { font-size: 16px; width: 24px; text-align: center; }
        .cap-title { font-size: 12px; font-weight: 500; color: #e2e8f0; }
        .cap-sub { font-size: 10px; color: #64748b; }
        
        .sidebar-footer { padding: 12px; margin-top: auto; }
        .new-chat-btn {
          width: 100%; padding: 8px; background: #f59e0b; border: none;
          color: #0f1117; font-weight: 600; font-size: 13px; border-radius: 8px;
          cursor: pointer; margin-bottom: 8px; transition: background 0.15s;
        }
        .new-chat-btn:hover { background: #fbbf24; }
        .model-badge { font-size: 10px; color: #475569; text-align: center; }
        
        /* Main */
        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        
        .chat-header {
          padding: 12px 20px;
          background: #161b27;
          border-bottom: 1px solid #1e2d40;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .header-left { display: flex; align-items: center; gap: 12px; }
        .header-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .header-title { font-size: 15px; font-weight: 600; color: #f59e0b; }
        .session-tag { font-size: 11px; color: #475569; font-family: monospace; background: #1e2d40; padding: 2px 8px; border-radius: 4px; }
        
        /* Tool badges */
        .tool-badge {
          display: flex; align-items: center; gap: 6px;
          background: #1e2d40; border: 1px solid #f59e0b33;
          color: #f59e0b; font-size: 11px; padding: 4px 10px; border-radius: 20px;
          animation: pulse 1.5s infinite;
        }
        .tool-spinner { animation: spin 1s linear infinite; display: inline-block; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        
        /* Messages */
        .messages {
          flex: 1; overflow-y: auto; padding: 20px;
          display: flex; flex-direction: column; gap: 16px;
        }
        .messages::-webkit-scrollbar { width: 6px; }
        .messages::-webkit-scrollbar-track { background: transparent; }
        .messages::-webkit-scrollbar-thumb { background: #263347; border-radius: 3px; }
        
        .message { display: flex; gap: 12px; align-items: flex-start; }
        .msg-avatar { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; background: #1e2d40; }
        .message.assistant .msg-avatar { background: #f59e0b22; }
        .msg-body { flex: 1; min-width: 0; }
        .msg-role { font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 4px; }
        .message.assistant .msg-role { color: #f59e0b; }
        
        .user-text { color: #e2e8f0; line-height: 1.6; font-size: 14px; }
        
        .message-content { color: #cbd5e1; font-size: 14px; line-height: 1.7; }
        
        /* Markdown styling */
        .md-h1 { font-size: 18px; font-weight: 700; color: #f8fafc; margin: 16px 0 8px; border-bottom: 1px solid #1e2d40; padding-bottom: 6px; }
        .md-h2 { font-size: 15px; font-weight: 600; color: #f1f5f9; margin: 12px 0 6px; }
        .md-h3 { font-size: 13px; font-weight: 600; color: #e2e8f0; margin: 10px 0 4px; }
        .md-p { margin: 4px 0; }
        .md-bold-p { font-weight: 600; color: #f8fafc; margin: 4px 0; }
        .md-li { margin: 3px 0 3px 20px; list-style: disc; }
        .md-ol { list-style: decimal; }
        .md-hr { border: none; border-top: 1px solid #1e2d40; margin: 12px 0; }
        .md-td { padding: 6px 12px; border: 1px solid #1e2d40; font-size: 13px; }
        
        .inline-code { background: #1e2d40; color: #f59e0b; padding: 1px 5px; border-radius: 4px; font-family: monospace; font-size: 12px; }
        
        /* Mermaid */
        .mermaid-container { margin: 12px 0; background: #0d1117; border: 1px solid #1e2d40; border-radius: 10px; overflow: hidden; }
        .mermaid-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; background: #161b27; font-size: 12px; color: #94a3b8; border-bottom: 1px solid #1e2d40; }
        .mermaid-code { padding: 14px; font-family: monospace; font-size: 12px; color: #7dd3fc; overflow-x: auto; white-space: pre; }
        .mermaid-hint { padding: 6px 14px; font-size: 11px; color: #475569; background: #0d1117; border-top: 1px solid #1e2d40; }
        .mermaid-hint a { color: #f59e0b; text-decoration: none; }
        .copy-btn { background: #1e2d40; border: 1px solid #263347; color: #94a3b8; font-size: 11px; padding: 2px 8px; border-radius: 4px; cursor: pointer; }
        .copy-btn:hover { color: #e2e8f0; }
        
        /* Cursor blink */
        .cursor-blink { animation: blink 1s step-end infinite; color: #f59e0b; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        
        /* Welcome */
        .welcome { text-align: center; padding: 60px 20px; max-width: 700px; margin: auto; }
        .welcome-icon { font-size: 48px; margin-bottom: 16px; }
        .welcome-title { font-size: 24px; font-weight: 700; color: #f59e0b; margin-bottom: 12px; }
        .welcome-sub { font-size: 14px; color: #64748b; line-height: 1.7; margin-bottom: 32px; }
        .welcome-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: left; }
        .welcome-card { background: #161b27; border: 1px solid #1e2d40; border-radius: 10px; padding: 14px; cursor: pointer; text-align: left; transition: all 0.2s; }
        .welcome-card:hover { border-color: #f59e0b55; background: #1a2234; }
        .wc-label { display: block; font-size: 13px; font-weight: 600; color: #e2e8f0; margin-bottom: 6px; }
        .wc-desc { display: block; font-size: 11px; color: #64748b; line-height: 1.5; }
        
        /* Input */
        .input-area { padding: 16px 20px; background: #161b27; border-top: 1px solid #1e2d40; }
        .input-box { display: flex; gap: 10px; align-items: flex-end; }
        .input-textarea {
          flex: 1; background: #0f1117; border: 1px solid #1e2d40;
          color: #e2e8f0; font-size: 14px; padding: 12px; border-radius: 10px;
          resize: none; outline: none; font-family: inherit; line-height: 1.5;
          transition: border-color 0.15s;
        }
        .input-textarea:focus { border-color: #f59e0b55; }
        .input-textarea::placeholder { color: #475569; }
        .input-textarea:disabled { opacity: 0.5; }
        
        .send-btn {
          width: 40px; height: 40px; background: #f59e0b; border: none;
          border-radius: 10px; color: #0f1117; font-size: 18px; cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          transition: all 0.15s; flex-shrink: 0;
        }
        .send-btn:hover:not(:disabled) { background: #fbbf24; transform: scale(1.05); }
        .send-btn:disabled { opacity: 0.4; cursor: default; transform: none; }
        .send-btn.loading { animation: spin 1s linear infinite; background: #1e2d40; color: #f59e0b; }
        
        .input-hint { font-size: 11px; color: #334155; text-align: center; margin-top: 8px; }
        
        @media (max-width: 640px) {
          .sidebar { display: none; }
          .welcome-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}
