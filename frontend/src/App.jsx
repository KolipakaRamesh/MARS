import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useQuery } from "convex/react";
import { api } from "@convex/_generated/api";
import { 
  Search, 
  Cpu, 
  Activity, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  Database,
  History,
  Layers,
  ShieldCheck,
  Zap,
  BarChart2,
  Bot,
  Radar
} from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

// Agent color map
const AGENT_COLORS = {
  planner:  { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', border: 'rgba(167,139,250,0.25)' },
  research: { color: '#38bdf8', bg: 'rgba(56,189,248,0.1)',  border: 'rgba(56,189,248,0.25)' },
  analyst:  { color: '#4ade80', bg: 'rgba(74,222,128,0.1)',  border: 'rgba(74,222,128,0.25)' },
  reviewer: { color: '#fb923c', bg: 'rgba(251,146,60,0.1)',  border: 'rgba(251,146,60,0.25)' },
};

function AgentUsageCard({ usage }) {
  const meta = AGENT_COLORS[usage.agent] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.2)' };
  const modelShort = usage.model ? usage.model.split('/').pop() : '—';

  return (
    <div className="agent-usage-card" style={{ borderColor: meta.border, background: meta.bg }}>
      <div className="agent-usage-header">
        <Bot size={14} style={{ color: meta.color, flexShrink: 0 }} />
        <span className="agent-usage-name" style={{ color: meta.color }}>
          {usage.agent}
        </span>
      </div>
      <div className="agent-usage-model" title={usage.model}>{modelShort}</div>
      <div className="agent-usage-stats">
        <div className="usage-stat">
          <span className="usage-stat-label">In</span>
          <span className="usage-stat-value">{(usage.prompt_tokens || 0).toLocaleString()}</span>
        </div>
        <div className="usage-stat">
          <span className="usage-stat-label">Out</span>
          <span className="usage-stat-value">{(usage.completion_tokens || 0).toLocaleString()}</span>
        </div>
        <div className="usage-stat">
          <span className="usage-stat-label">ms</span>
          <span className="usage-stat-value">{Math.round(usage.latency_ms || 0).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}

function LiveStatusIndicator({ sessionId }) {
  // Real-time status query from Convex
  const status = useQuery(api.heartbeats.getStatus, sessionId ? { session_id: sessionId } : "skip");

  if (!sessionId || !status) return null;

  const isActive = status.agent !== 'done' && status.agent !== 'error';
  const meta = AGENT_COLORS[status.agent] || { color: 'var(--accent-blue)' };

  return (
    <div className={`live-status-bar fade-in ${isActive ? 'active' : ''}`}>
      <div className="live-status-indicator">
        {isActive ? <Radar size={16} className="pulse" style={{ color: meta.color }} /> : <CheckCircle2 size={16} className="text-green" />}
        <span className="live-status-text">
          {status.status}
        </span>
      </div>
      {status.subtask_index !== undefined && isActive && (
         <div className="live-status-subtask">
            Subtask {status.subtask_index + 1}
         </div>
      )}
    </div>
  );
}

function App() {
  const [query, setQuery] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Real-time session history from Convex
  const history = useQuery(api.sessions.getRecentSessions, { limit: 15 }) || [];

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim() || loading) return;

    const sessionId = `mars-${Date.now()}`;
    setCurrentSessionId(sessionId);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
           query, 
           session_id: sessionId,
           max_iterations: 3 
        }),
      });

      if (!resp.ok) {
        throw new Error(`API Error: ${resp.statusText}`);
      }

      const data = await resp.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSession = (session) => {
    setResult({
      query: session.query,
      answer: session.synthesized_answer || "Session data incomplete",
      quality_score: session.quality_score,
      verdict: session.verdict,
      subtasks: session.subtasks || [],
      iteration_count: session.iteration_count || 1,
      llm_usage: [],   
    });
    setQuery(session.query);
    setCurrentSessionId(session.session_id);
  };

  // Aggregate totals across all llm_usage entries
  const usageTotals = result?.llm_usage?.length
    ? result.llm_usage.reduce(
        (acc, u) => ({
          total_tokens: acc.total_tokens + (u.total_tokens || 0),
          latency_ms:   acc.latency_ms   + (u.latency_ms   || 0),
        }),
        { total_tokens: 0, latency_ms: 0 }
      )
    : null;

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="logo-area">
          <Cpu className="logo-icon" size={32} />
          <span className="logo-text">MARS</span>
        </div>
        <div className="header-status">
          <ShieldCheck size={20} className={result ? "text-green" : "text-dim"} />
        </div>
      </header>

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-section">
          <div className="sidebar-title">
            <History size={14} style={{ marginRight: '8px' }} />
            Recent Sessions (Live)
          </div>
          <div className="history-list">
            {history.length > 0 ? history.map((s, i) => (
              <div 
                key={s._id || i} 
                className={`history-item ${currentSessionId === s.session_id ? 'active' : ''}`} 
                onClick={() => loadSession(s)}
                title={s.query}
              >
                {s.query}
              </div>
            )) : (
              <div className="history-item empty">No history yet</div>
            )}
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-title">
            <Layers size={14} style={{ marginRight: '8px' }} />
            Research Plan
          </div>
          <div className="subtask-list">
            {result?.subtasks ? result.subtasks.map((task, i) => (
              <div key={i} className={`subtask-item ${loading ? 'active pulse' : 'completed'}`}>
                <CheckCircle2 size={16} className="subtask-icon text-accent" />
                <span className="subtask-text">{task}</span>
              </div>
            )) : loading ? (
              <div className="subtask-item active pulse">
                <Activity size={16} className="subtask-icon" />
                <span className="subtask-text">Decomposing query...</span>
              </div>
            ) : (
              <div className="subtask-item empty">Enter a query to see the plan</div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Search Bar */}
        <div className="search-container fade-in">
          <form onSubmit={handleSearch} className="search-input-wrapper">
            <Search className="text-secondary" size={24} />
            <input 
              type="text" 
              className="search-input" 
              placeholder="What would you like to research today?" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="search-button" disabled={loading || !query.trim()}>
              {loading ? 'Analyzing...' : 'Execute'}
            </button>
          </form>
        </div>

        {/* Live Status Bar (Convex powered) */}
        <LiveStatusIndicator sessionId={currentSessionId} />

        {/* Error Handling */}
        {error && (
          <div className="metric-card verdict-escalate fade-in" style={{ borderColor: '#f87171' }}>
            <div className="metric-label" style={{ color: '#f87171' }}>Error Encountered</div>
            <div className="text-primary">{error}</div>
          </div>
        )}

        {/* Results Area */}
        {result && (
          <>
            {/* Quality Metrics */}
            <div className="metrics-row fade-in">
              <div className="metric-card">
                <div className="metric-label">Quality Score</div>
                <div className="metric-value">{(result.quality_score * 100).toFixed(0)}%</div>
                <div className="progress-bar-bg" style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }}>
                  <div className="progress-bar-fill" style={{ 
                    height: '100%', 
                    width: `${result.quality_score * 100}%`,
                    background: 'var(--accent-blue)',
                    borderRadius: '2px'
                  }}></div>
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Review Verdict</div>
                <div className="metric-value">
                  <span className={`verdict-tag verdict-${result.verdict?.toLowerCase()}`}>
                    {result.verdict}
                  </span>
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Iterations</div>
                <div className="metric-value">{result.iteration_count}</div>
              </div>
              {usageTotals && (
                <>
                  <div className="metric-card">
                    <div className="metric-label"><Zap size={11} style={{display:'inline',marginRight:4}}/>Total Tokens</div>
                    <div className="metric-value">{usageTotals.total_tokens.toLocaleString()}</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label"><Clock size={11} style={{display:'inline',marginRight:4}}/>Total Latency</div>
                    <div className="metric-value">{(usageTotals.latency_ms / 1000).toFixed(1)}s</div>
                  </div>
                </>
              )}
            </div>

            {/* Live Agent Usage Breakdown */}
            {result.llm_usage?.length > 0 && (
              <div className="fade-in">
                <div className="section-title">
                  <BarChart2 size={14} style={{ marginRight: '8px' }} />
                  Agent Metrics Breakdown
                </div>
                <div className="agent-usage-grid">
                  {result.llm_usage.map((u, i) => (
                    <AgentUsageCard key={i} usage={u} />
                  ))}
                </div>
              </div>
            )}

            {/* Markdown Answer */}
            <div className="results-card fade-in">
              <div className="markdown-content">
                <ReactMarkdown>{result.answer}</ReactMarkdown>
              </div>
            </div>
          </>
        )}

        {/* Empty State */}
        {!result && !loading && !error && (
          <div className="empty-state fade-in" style={{ textAlign: 'center', marginTop: '4rem', opacity: 0.5 }}>
            <Database size={64} style={{ marginBottom: '1rem', color: 'var(--accent-blue)' }} />
            <h2 className="text-primary">Multi-Agent Research System</h2>
            <p className="text-secondary">Ready to synthesize information from across the web</p>
          </div>
        )}

        {/* Loading State */}
        {loading && !result && (
          <div className="loading-state fade-in" style={{ textAlign: 'center', marginTop: '4rem' }}>
            <div className="pulse" style={{ marginBottom: '1.5rem' }}>
              <Cpu size={64} style={{ color: 'var(--accent-blue)' }} />
            </div>
            <h2 className="text-primary">Agents are working...</h2>
            <p className="text-secondary">This may take a minute as researchers gather facts</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
