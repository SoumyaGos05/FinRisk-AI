/**
 * FinRisk AI — Root Application Component
 *
 * Single-page application with smooth in-page section navigation.
 * Sections: Home, Analyze, Results, How It Works, Responsible AI, SDG 12, About
 */

import { useState, useCallback } from 'react';
import './index.css';
import { apiBase } from './api.js';

// ── Demo Data ────────────────────────────────────────────────────────────────

const DEMO_DATA = {
  company_name: 'Demo Manufacturing Ltd.',
  current_revenue: '10000000',
  previous_revenue: '10800000',
  current_net_profit: '500000',
  previous_net_profit: '590000',
  total_debt: '2500000',
  shareholders_equity: '1000000',
  current_assets: '1200000',
  current_liabilities: '1500000',
};

// ── Utility helpers ───────────────────────────────────────────────────────────

function fmt(n) {
  if (n === null || n === undefined || n === '') return '—';
  const num = typeof n === 'string' ? parseFloat(n) : n;
  if (isNaN(num)) return '—';
  return new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 }).format(num);
}

function fmtChange(current, previous) {
  const c = parseFloat(current);
  const p = parseFloat(previous);
  if (!isFinite(c) || !isFinite(p) || p === 0) return null;
  const pct = ((c - p) / Math.abs(p)) * 100;
  return { pct: Math.abs(pct).toFixed(1), up: pct >= 0 };
}

// ── SVG Risk Gauge ────────────────────────────────────────────────────────────

function RiskGauge({ level }) {
  const palettes = {
    LOW:      { track: '#e5e7eb', fill: '#059669', needle: '#059669', label: 'LOW' },
    MODERATE: { track: '#e5e7eb', fill: '#d97706', needle: '#d97706', label: 'MODERATE' },
    HIGH:     { track: '#e5e7eb', fill: '#dc2626', needle: '#dc2626', label: 'HIGH' },
  };
  const p = palettes[level] || palettes.MODERATE;

  // 240° arc from 210° to 330° (going clockwise through the top)
  const cx = 130, cy = 120, r = 88;
  const toRad = (d) => (d * Math.PI) / 180;

  // Full track arc path: start at 210°, sweep 240° to 30° (short way around = large-arc=1)
  const ax = (deg) => cx + r * Math.cos(toRad(deg));
  const ay = (deg) => cy + r * Math.sin(toRad(deg));
  const trackD = `M ${ax(210)} ${ay(210)} A ${r} ${r} 0 1 1 ${ax(30)} ${ay(30)}`;

  // Colored fill based on level
  // LOW: 210° → 270° (60° of 240° = 1/4)
  // MODERATE: 210° → 330° (but 330=30+300… let's do 210→-30 which is 0°-90° of meter)
  // HIGH: full arc 210→30 (large)
  const fillArcs = {
    LOW:      `M ${ax(210)} ${ay(210)} A ${r} ${r} 0 0 1 ${ax(290)} ${ay(290)}`,
    MODERATE: `M ${ax(210)} ${ay(210)} A ${r} ${r} 0 0 1 ${ax(10)} ${ay(10)}`,
    HIGH:     `M ${ax(210)} ${ay(210)} A ${r} ${r} 0 1 1 ${ax(30)} ${ay(30)}`,
  };

  // Needle angle: LOW=-90°+(-60°)=-150° → but we want visual mapping
  // Gauge spans 210° to 30° = 240° sweep; LOW=left, HIGH=right
  // LOW: 210°+40°=250°, MODERATE: 270°, HIGH: 210°+200°=50° on circle
  const needleDeg = { LOW: 250, MODERATE: 270, HIGH: 30 };
  const nd = needleDeg[level] ?? 270;
  const nx = cx + 72 * Math.cos(toRad(nd));
  const ny = cy + 72 * Math.sin(toRad(nd));

  return (
    <svg
      width="260"
      height="160"
      viewBox="0 0 260 160"
      className="gauge-svg"
      aria-label={`Risk gauge showing ${level} risk`}
      role="img"
    >
      {/* Track */}
      <path d={trackD} fill="none" stroke="#e5e7eb" strokeWidth="14" strokeLinecap="round" />
      {/* Colored fill */}
      <path d={fillArcs[level] || fillArcs.MODERATE} fill="none" stroke={p.fill} strokeWidth="14" strokeLinecap="round" />
      {/* Zone text */}
      <text x="24" y="148" fontSize="9.5" fill="#059669" fontWeight="700" fontFamily="-apple-system,system-ui,sans-serif">LOW</text>
      <text x="115" y="30"  fontSize="9.5" fill="#d97706" fontWeight="700" fontFamily="-apple-system,system-ui,sans-serif" textAnchor="middle">MOD</text>
      <text x="234" y="148" fontSize="9.5" fill="#dc2626" fontWeight="700" fontFamily="-apple-system,system-ui,sans-serif" textAnchor="end">HIGH</text>
      {/* Needle */}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={p.needle} strokeWidth="2.5" strokeLinecap="round" />
      {/* Hub */}
      <circle cx={cx} cy={cy} r="7" fill={p.fill} />
      <circle cx={cx} cy={cy} r="3" fill="#fff" />
      {/* Center readout */}
      <text x={cx} y={cy + 34} fontSize="12.5" fontWeight="800" fill={p.fill} textAnchor="middle" fontFamily="-apple-system,system-ui,sans-serif">{p.label}</text>
    </svg>
  );
}

// ── Navigation ────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: 'home',           label: 'Home' },
  { id: 'analyze',        label: 'Analyze' },
  { id: 'how-it-works',   label: 'How It Works' },
  { id: 'responsible-ai', label: 'Responsible AI' },
  { id: 'sdg12',          label: 'SDG 12' },
  { id: 'about',          label: 'About' },
];

function Nav({ activeSection, onNav, onStartAnalysis }) {
  const [open, setOpen] = useState(false);

  const handleNav = (id) => {
    setOpen(false);
    onNav(id);
  };

  const handleStart = () => {
    setOpen(false);
    onStartAnalysis();
  };

  return (
    <>
      <nav className="nav">
        <div className="nav-inner">
          <div className="nav-brand" onClick={() => handleNav('home')} role="button" tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && handleNav('home')}>
            <span className="nav-brand-dot" aria-hidden="true" />
            FinRisk AI
          </div>

          {/* Desktop links */}
          <ul className="nav-links" role="list">
            {NAV_ITEMS.map((item) => (
              <li key={item.id}>
                <button
                  className={activeSection === item.id ? 'active' : ''}
                  onClick={() => onNav(item.id)}
                  aria-current={activeSection === item.id ? 'page' : undefined}
                >
                  {item.label}
                </button>
              </li>
            ))}
            <li>
              <button className="nav-cta" onClick={onStartAnalysis} aria-label="Start financial risk analysis">
                Start Analysis
              </button>
            </li>
          </ul>

          {/* Mobile toggle */}
          <button
            className={`nav-toggle${open ? ' open' : ''}`}
            onClick={() => setOpen(!open)}
            aria-label={open ? 'Close navigation' : 'Open navigation'}
            aria-expanded={open}
          >
            <span className="nav-toggle-bar" />
            <span className="nav-toggle-bar" />
            <span className="nav-toggle-bar" />
          </button>
        </div>
      </nav>

      {/* Mobile drawer */}
      <div className={`nav-drawer${open ? ' open' : ''}`} aria-hidden={!open}>
        <ul>
          {NAV_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                className={activeSection === item.id ? 'active' : ''}
                onClick={() => handleNav(item.id)}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
        <button className="nav-drawer-cta" onClick={handleStart}>
          Start Analysis →
        </button>
      </div>
    </>
  );
}

// ── Home Section ──────────────────────────────────────────────────────────────

const HERO_METRICS = [
  { icon: '📈', name: 'Revenue Growth',    formula: '(Curr − Prev) / Prev × 100' },
  { icon: '💰', name: 'Profit Growth',     formula: '(Curr − Prev) / Prev × 100' },
  { icon: '⚖️', name: 'Debt-to-Equity',   formula: 'Total Debt / Equity' },
  { icon: '🏦', name: 'Current Ratio',     formula: 'Assets / Liabilities' },
  { icon: '📊', name: 'Net Profit Margin', formula: 'Net Profit / Revenue × 100' },
];

function HomeSection({ onStartAnalysis, onNav }) {
  return (
    <section id="home">
      {/* Hero */}
      <div className="hero">
        <div className="hero-inner">
          <div className="hero-eyebrow">
            <span className="nav-brand-dot" aria-hidden="true" />
            Prototype Financial Risk Analysis
          </div>

          <h1 className="hero-title">
            <span className="hero-title-accent">FinRisk AI</span>
            Understand financial risk<br />before it becomes a problem.
          </h1>

          <p className="hero-description">
            Enter a company&rsquo;s basic financial information and receive a transparent,
            deterministic Prototype Financial Risk Indicator with explanations for every metric.
          </p>

          <div className="hero-actions">
            <button className="btn-primary" onClick={onStartAnalysis} aria-label="Go to analysis form">
              Start Analysis →
            </button>
            <button className="btn-secondary" onClick={() => onNav('how-it-works')}>
              How It Works
            </button>
          </div>

          <div className="hero-metrics-preview" aria-label="Five financial metrics used in analysis">
            {HERO_METRICS.map((m) => (
              <div key={m.name} className="hero-metric-chip">
                <div className="hero-metric-chip-icon" aria-hidden="true">{m.icon}</div>
                <div className="hero-metric-chip-name">{m.name}</div>
                <div className="hero-metric-chip-formula">{m.formula}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Responsible AI preview */}
      <div className="home-rai-section">
        <div className="section-inner">
          <div className="section-label">Responsible AI</div>
          <h2 className="section-title">Built for transparency, not automation</h2>
          <p className="section-subtitle" style={{ marginBottom: '28px' }}>
            All five financial metrics and the Prototype Financial Risk Indicator are computed deterministically.
            Gemini AI is used separately to generate an optional plain-language explanation of those already-calculated results —
            it does not calculate, modify, or override any metric value or risk classification.
          </p>
          <div className="card-grid">
            {[
              { icon: '🔢', title: 'Deterministic',          desc: 'All five metrics are computed using fixed arithmetic formulas. Same inputs always produce identical outputs.' },
              { icon: '🏷️', title: 'Transparent Thresholds', desc: 'Every threshold is clearly labelled as a prototype threshold and explained in plain English — not hidden in a model.' },
              { icon: '💡', title: 'Explainable Results',     desc: 'The results page shows which metrics contributed to the risk level and exactly why each was classified LOW, MODERATE, or HIGH.' },
              { icon: '👤', title: 'Human Oversight',         desc: 'FinRisk AI is a decision-support prototype. All financial decisions remain the responsibility of qualified professionals.' },
            ].map((c) => (
              <div key={c.title} className="card">
                <div style={{ fontSize: '22px', marginBottom: '10px' }} aria-hidden="true">{c.icon}</div>
                <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '6px', color: 'var(--color-text)' }}>{c.title}</div>
                <div style={{ fontSize: '12.5px', color: 'var(--color-text-secondary)', lineHeight: '1.6' }}>{c.desc}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '22px' }}>
            <span className="rai-badge">
              <span className="rai-badge-dot" aria-hidden="true" />
              Prototype decision-support system — not financial advice
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Analyze Section ────────────────────────────────────────────────────────────

const INITIAL_FORM = {
  company_name: '',
  current_revenue: '',
  previous_revenue: '',
  current_net_profit: '',
  previous_net_profit: '',
  total_debt: '',
  shareholders_equity: '',
  current_assets: '',
  current_liabilities: '',
};

function validateForm(values) {
  const errors = {};
  if (!values.company_name.trim()) errors.company_name = 'Company name is required.';

  const numericFields = [
    ['current_revenue',    'Current Revenue',     false, 'nonzero'],
    ['previous_revenue',   'Previous Revenue',    false, 'nonzero'],
    ['current_net_profit', 'Current Net Profit',  true,  null],
    ['previous_net_profit','Previous Net Profit', true,  'nonzero'],
    ['total_debt',         'Total Debt',          false, null],
    ['shareholders_equity',"Shareholders' Equity",true,  'nonzero'],
    ['current_assets',     'Current Assets',      false, null],
    ['current_liabilities','Current Liabilities', false, 'positive'],
  ];

  for (const [key, label, allowNegative, special] of numericFields) {
    const v = values[key].trim();
    if (v === '') {
      errors[key] = `${label} is required.`;
    } else {
      const num = parseFloat(v);
      if (isNaN(num)) {
        errors[key] = `${label} must be a number.`;
      } else if (!allowNegative && num < 0) {
        errors[key] = `${label} cannot be negative.`;
      } else if (special === 'nonzero' && num === 0) {
        errors[key] = `${label} cannot be zero.`;
      } else if (special === 'positive' && num <= 0) {
        errors[key] = `${label} must be positive.`;
      }
    }
  }
  return errors;
}

function FormField({ id, label, hint, value, onChange, error, placeholder, required = true, type = 'number' }) {
  return (
    <div className="form-field">
      <label className="form-label" htmlFor={id}>
        {label}
        {hint && <span className="form-label-hint">{hint}</span>}
      </label>
      <input
        id={id}
        type={type}
        className={`form-input${error ? ' error' : ''}`}
        value={value}
        onChange={(e) => onChange(id, e.target.value)}
        placeholder={placeholder || '0'}
        step={type === 'number' ? 'any' : undefined}
        required={required}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${id}-error` : undefined}
      />
      {error && (
        <div id={`${id}-error`} className="form-error" role="alert">
          <span aria-hidden="true">⚠</span> {error}
        </div>
      )}
    </div>
  );
}

function AnalyzeSection({ onResults, isDemoLoaded, setIsDemoLoaded }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const handleChange = useCallback((id, value) => {
    setForm((prev) => ({ ...prev, [id]: value }));
    setErrors((prev) => { const n = { ...prev }; delete n[id]; return n; });
  }, []);

  const handleDemo = useCallback(() => {
    setForm(DEMO_DATA);
    setErrors({});
    setApiError('');
    setIsDemoLoaded(true);
  }, [setIsDemoLoaded]);

  const handleReset = useCallback(() => {
    setForm(INITIAL_FORM);
    setErrors({});
    setApiError('');
    setIsDemoLoaded(false);
  }, [setIsDemoLoaded]);

  const handleSubmit = useCallback(async () => {
    const validationErrors = validateForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setLoading(true);
    setApiError('');

    const payload = {
      company_name:        form.company_name.trim(),
      current_revenue:     parseFloat(form.current_revenue),
      previous_revenue:    parseFloat(form.previous_revenue),
      current_net_profit:  parseFloat(form.current_net_profit),
      previous_net_profit: parseFloat(form.previous_net_profit),
      total_debt:          parseFloat(form.total_debt),
      shareholders_equity: parseFloat(form.shareholders_equity),
      current_assets:      parseFloat(form.current_assets),
      current_liabilities: parseFloat(form.current_liabilities),
    };

    try {
      const base = apiBase || 'http://localhost:8000';
      const res = await fetch(`${base}/risk/financial`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const msg = data?.detail
          ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
          : `Server error (${res.status})`;
        setApiError(msg);
        setLoading(false);
        return;
      }
      const result = await res.json();
      onResults(result, isDemoLoaded);
    } catch {
      setApiError('Unable to reach the server. Please ensure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }, [form, onResults, isDemoLoaded]);

  const hasAnyValue = Object.values(form).some((v) => v !== '');

  return (
    <section id="analyze" className="section" style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}>
      <div className="section-inner">
        <div className="section-label">Analyze</div>
        <h2 className="section-title">Financial Risk Analysis</h2>
        <p className="section-subtitle" style={{ marginBottom: '32px' }}>
          Enter the company&rsquo;s financial figures below. All nine fields are required.
          Your inputs are used to calculate the prototype indicators shown below.
        </p>

        <div className="analyze-layout">
          {/* Form column */}
          <div>
            {isDemoLoaded && (
              <div className="demo-banner" role="status">
                ⚠ SYNTHETIC DEMONSTRATION DATA — Demo Manufacturing Ltd. is a fictional company.
              </div>
            )}

            <div className="form-card">
              <div className="form-group-full">
                <FormField
                  id="company_name"
                  label="Company Name"
                  hint="Name of the company being analysed"
                  value={form.company_name}
                  onChange={handleChange}
                  error={errors.company_name}
                  placeholder="e.g. Acme Corp Ltd."
                  type="text"
                />
              </div>

              <div className="form-section-title" aria-label="Revenue fields">Revenue</div>
              <div className="form-group">
                <FormField id="current_revenue"  label="Current Revenue"  hint="Most recent period total revenue"       value={form.current_revenue}  onChange={handleChange} error={errors.current_revenue}  placeholder="e.g. 10000000" />
                <FormField id="previous_revenue" label="Previous Revenue" hint="Prior period revenue — must not be zero" value={form.previous_revenue} onChange={handleChange} error={errors.previous_revenue} placeholder="e.g. 10800000" />
              </div>

              <div className="form-section-title" aria-label="Profitability fields">Profitability</div>
              <div className="form-group">
                <FormField id="current_net_profit"  label="Current Net Profit"  hint="Most recent net profit (may be negative)" value={form.current_net_profit}  onChange={handleChange} error={errors.current_net_profit}  placeholder="e.g. 500000" />
                <FormField id="previous_net_profit" label="Previous Net Profit" hint="Prior period net profit — must not be zero" value={form.previous_net_profit} onChange={handleChange} error={errors.previous_net_profit} placeholder="e.g. 590000" />
              </div>

              <div className="form-section-title" aria-label="Balance sheet fields">Balance Sheet</div>
              <div className="form-group">
                <FormField id="total_debt"          label="Total Debt"             hint="Total outstanding debt (≥ 0)"               value={form.total_debt}          onChange={handleChange} error={errors.total_debt}          placeholder="e.g. 2500000" />
                <FormField id="shareholders_equity" label="Shareholders' Equity"   hint="Total shareholders' equity — must not be zero" value={form.shareholders_equity} onChange={handleChange} error={errors.shareholders_equity} placeholder="e.g. 1000000" />
              </div>

              <div className="form-section-title" aria-label="Liquidity fields">Liquidity</div>
              <div className="form-group">
                <FormField id="current_assets"      label="Current Assets"      hint="Total current assets (≥ 0)"            value={form.current_assets}      onChange={handleChange} error={errors.current_assets}      placeholder="e.g. 1200000" />
                <FormField id="current_liabilities" label="Current Liabilities" hint="Total current liabilities — must be > 0" value={form.current_liabilities} onChange={handleChange} error={errors.current_liabilities} placeholder="e.g. 1500000" />
              </div>

              {apiError && <div className="error-box" role="alert">{apiError}</div>}

              <div className="form-actions">
                <button className="btn-analyze" onClick={handleSubmit} disabled={loading} aria-busy={loading}>
                  {loading ? (
                    <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} aria-hidden="true" /> Analysing…</>
                  ) : 'Run Analysis →'}
                </button>
                <button className="btn-demo" onClick={handleDemo} title="Load synthetic demonstration data">
                  Load Demo Data
                </button>
                {hasAnyValue && (
                  <button className="btn-secondary" onClick={handleReset} style={{ fontSize: '13px', padding: '9px 16px' }} aria-label="Clear all form fields">
                    Clear
                  </button>
                )}
              </div>

              <p className="form-note">
                ⓘ Your inputs are sent to the local analysis server for calculation only and are not stored.
              </p>
            </div>
          </div>

          {/* Sidebar */}
          <div>
            <div className="sidebar-card" aria-label="Metrics reference">
              <div className="sidebar-title">Five metrics calculated</div>
              {[
                ['Revenue Growth',    '(Current − Prev) / Prev × 100'],
                ['Profit Growth',     '(Current − Prev) / Prev × 100'],
                ['Debt-to-Equity',    'Total Debt / Shareholders\' Equity'],
                ['Current Ratio',     'Current Assets / Current Liabilities'],
                ['Net Profit Margin', 'Net Profit / Revenue × 100'],
              ].map(([name, formula], i) => (
                <div key={name} className="sidebar-item">
                  <div className="sidebar-item-number" aria-hidden="true">{i + 1}</div>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--color-text)', fontSize: '13px' }}>{name}</div>
                    <div style={{ fontSize: '10.5px', color: 'var(--color-text-muted)', marginTop: '2px' }}>{formula}</div>
                  </div>
                </div>
              ))}
              <div style={{ marginTop: '18px', fontSize: '11.5px', color: 'var(--color-text-muted)', lineHeight: '1.55', padding: '12px', background: 'var(--color-surface)', borderRadius: 'var(--radius-sm)' }}>
                <strong style={{ color: 'var(--color-text)' }}>Prototype thresholds</strong> are used for demonstration only and are not universal financial standards.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Results Section ────────────────────────────────────────────────────────────

function TrendBar({ current, previous, label }) {
  const c = parseFloat(current);
  const p = parseFloat(previous);
  if (!isFinite(c) || !isFinite(p) || p <= 0) return null;
  const up = c >= p;
  const ratio = Math.max(c, p) > 0 ? Math.min(c / Math.max(c, p), 1) : 0.5;
  const prevH = p >= c ? 28 : Math.round(ratio * 28);
  const currH = c >= p ? 28 : Math.round(ratio * 28);
  return (
    <div style={{ marginTop: '14px' }}>
      <div className="trend-bar-container" aria-hidden="true">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
          <div className="trend-bar trend-bar-prev" style={{ height: `${prevH}px` }} />
          <div className="trend-bar-label">Prev</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
          <div className={`trend-bar ${up ? 'trend-bar-curr-up' : 'trend-bar-curr-down'}`} style={{ height: `${currH}px` }} />
          <div className="trend-bar-label">Curr</div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ m }) {
  const [showThreshold, setShowThreshold] = useState(false);
  return (
    <div className={`metric-card ${m.level}`} aria-label={`${m.name}: ${m.formatted_value}, ${m.level} risk`}>
      <div className="metric-card-header">
        <span className="metric-card-name">{m.name}</span>
        <span className={`metric-level-chip ${m.level}`} aria-label={`Risk level: ${m.level}`}>{m.level}</span>
      </div>
      <div className="metric-card-value">{m.formatted_value}</div>
      <div className="metric-card-explanation">{m.explanation}</div>
      <button
        className="metric-threshold-toggle"
        onClick={() => setShowThreshold((v) => !v)}
        aria-expanded={showThreshold}
        aria-label={`${showThreshold ? 'Hide' : 'Show'} prototype threshold for ${m.name}`}
      >
        {showThreshold ? '▲ Hide threshold' : '▼ Prototype threshold'}
      </button>
      {showThreshold && <div className="metric-threshold-note">{m.threshold_note}</div>}
    </div>
  );
}

// ── AI Explanation Panel ───────────────────────────────────────────────────────

/**
 * Displays the optional AI-generated explanation returned by the backend.
 * The deterministic analysis is always shown — this panel is supplemental only.
 *
 * @param {{ aiExplanation: object|null }} props
 */
function AIExplanationPanel({ aiExplanation }) {
  if (!aiExplanation) return null;

  return (
    <div className="ai-explanation-panel" aria-label="AI-Assisted Explanation">
      <div className="ai-explanation-header">
        <span className="ai-explanation-badge" aria-hidden="true">AI</span>
        <span className="ai-explanation-title">AI-Assisted Explanation</span>
      </div>

      {aiExplanation.available && aiExplanation.text ? (
        <>
          <p className="ai-explanation-text">{aiExplanation.text}</p>
          <p className="ai-explanation-disclosure">
            Generated from deterministic FinRisk AI metrics.
            AI output is explanatory only and should be independently reviewed.
            This is not investment, lending, credit, or professional financial advice.
          </p>
        </>
      ) : (
        <p className="ai-explanation-unavailable">
          AI explanation is temporarily unavailable. The deterministic financial analysis above is still complete and authoritative.
        </p>
      )}
    </div>
  );
}

// ── Results Section ────────────────────────────────────────────────────────────

function ResultsSection({ result, isDemo, onNewAnalysis }) {
  const [expandedFactors, setExpandedFactors] = useState({});
  const [whyOpen, setWhyOpen] = useState(false);

  if (!result) {
    return (
      <section id="results" className="section">
        <div className="section-inner">
          <div className="empty-state">
            <div className="empty-state-icon" aria-hidden="true">📊</div>
            <h2 className="empty-state-title">No analysis yet</h2>
            <p className="empty-state-desc">
              Complete the financial analysis form to see your Prototype Financial Risk Indicator here.
            </p>
            <button className="btn-primary" onClick={onNewAnalysis}>
              Start Analysis →
            </button>
          </div>
        </div>
      </section>
    );
  }

  const {
    company_name, overall_risk, overall_explanation, metrics,
    current_revenue, previous_revenue, current_net_profit, previous_net_profit,
  } = result;

  const revChange    = fmtChange(current_revenue, previous_revenue);
  const profitChange = fmtChange(current_net_profit, previous_net_profit);

  const sortedMetrics = [...metrics].sort((a, b) => {
    const order = { HIGH: 0, MODERATE: 1, LOW: 2 };
    return (order[a.level] ?? 3) - (order[b.level] ?? 3);
  });

  const toggleFactor = (name) =>
    setExpandedFactors((prev) => ({ ...prev, [name]: !prev[name] }));

  const riskIcons = { LOW: '✓', MODERATE: '⚠', HIGH: '✕' };

  return (
    <section id="results" className="section" style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}>
      <div className="section-inner">
        {isDemo && (
          <div className="demo-banner" role="status">
            ⚠ SYNTHETIC DEMONSTRATION DATA — Results based on Demo Manufacturing Ltd., a fictional company.
          </div>
        )}

        <div className="prototype-note">
          <strong>Prototype Financial Risk Indicator</strong> — All thresholds are prototype thresholds and are
          not universal financial standards. This system does not provide investment, lending, credit, or professional financial advice.
        </div>

        {/* Hero band: company + gauge + badge */}
        <div className="results-hero-band">
          <div className="results-company-block">
            <div className="results-company-label">Analysis Results</div>
            <div className="results-company-name">{company_name}</div>
          </div>

          <div className="gauge-container">
            <RiskGauge level={overall_risk} />
          </div>

          <div className="results-indicator-block">
            <div className="results-indicator-label">Prototype Financial Risk Indicator</div>
            <div className={`risk-badge ${overall_risk}`} role="status" aria-label={`Overall risk: ${overall_risk}`}>
              <span className="risk-badge-icon" aria-hidden="true">{riskIcons[overall_risk]}</span>
              {overall_risk}
            </div>
          </div>
        </div>

        {/* Trend comparison */}
        <div className="trend-cards">
          <div className="trend-card">
            <div className="trend-card-label">Revenue</div>
            <div className="trend-row">
              <span className="trend-value">{fmt(previous_revenue)}</span>
              <span className="trend-arrow" aria-hidden="true">→</span>
              <span className="trend-value">{fmt(current_revenue)}</span>
              {revChange && (
                <span className={`trend-change ${revChange.up ? 'up' : 'down'}`}>
                  {revChange.up ? '↑' : '↓'} {revChange.pct}%
                </span>
              )}
            </div>
            <TrendBar current={current_revenue} previous={previous_revenue} label="Revenue" />
          </div>
          <div className="trend-card">
            <div className="trend-card-label">Net Profit</div>
            <div className="trend-row">
              <span className="trend-value">{fmt(previous_net_profit)}</span>
              <span className="trend-arrow" aria-hidden="true">→</span>
              <span className="trend-value">{fmt(current_net_profit)}</span>
              {profitChange && (
                <span className={`trend-change ${profitChange.up ? 'up' : 'down'}`}>
                  {profitChange.up ? '↑' : '↓'} {profitChange.pct}%
                </span>
              )}
            </div>
            <TrendBar current={current_net_profit} previous={previous_net_profit} label="Profit" />
          </div>
        </div>

        {/* Five metric cards */}
        <div className="results-grid">
          {metrics.map((m) => <MetricCard key={m.name} m={m} />)}
        </div>

        {/* Why this risk */}
        <div className="why-risk-section">
          <div
            className="why-risk-title"
            role="button"
            tabIndex={0}
            aria-expanded={whyOpen}
            onClick={() => setWhyOpen((v) => !v)}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setWhyOpen((v) => !v)}
            style={{ cursor: 'pointer', userSelect: 'none' }}
          >
            <span aria-hidden="true">🔍</span> Why this risk level?
            <span
              className={`factor-expand-icon${whyOpen ? ' open' : ''}`}
              aria-hidden="true"
              style={{ marginLeft: 'auto' }}
            >
              ▼
            </span>
          </div>
          {whyOpen && (
            <>
              <p className="why-risk-explanation">{overall_explanation}</p>
              <div className="contributing-factors" role="list">
                {sortedMetrics.map((m) => (
                  <div
                    key={m.name}
                    className="factor-row"
                    role="listitem button"
                    tabIndex={0}
                    onClick={() => toggleFactor(m.name)}
                    onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && toggleFactor(m.name)}
                    aria-expanded={expandedFactors[m.name] || false}
                    aria-label={`${m.name}: ${m.formatted_value}, ${m.level}. Click to expand explanation.`}
                  >
                    <div className={`factor-level-dot ${m.level}`} aria-hidden="true" />
                    <div className="factor-content">
                      <div className="factor-header">
                        <div className="factor-name">{m.name}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span className="factor-value">{m.formatted_value}</span>
                          <span className={`factor-chip ${m.level}`}>{m.level}</span>
                        </div>
                      </div>
                      <div className="factor-detail">{m.explanation}</div>
                      {expandedFactors[m.name] && (
                        <div className="factor-expanded">{m.threshold_note}</div>
                      )}
                    </div>
                    <span
                      className={`factor-expand-icon${expandedFactors[m.name] ? ' open' : ''}`}
                      aria-hidden="true"
                    >
                      ▼
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <AIExplanationPanel aiExplanation={result.ai_explanation} />

        <div className="results-actions">
          <button className="btn-primary" onClick={onNewAnalysis}>
            New Analysis →
          </button>
        </div>
      </div>
    </section>
  );
}

// ── How It Works Section ───────────────────────────────────────────────────────

const PROCESS_STEPS = [
  { num: '1', title: 'Financial Information', desc: 'Enter 9 financial figures: revenue, profit, debt, equity, assets, liabilities.' },
  { num: '2', title: 'Five Core Metrics',     desc: 'Revenue Growth, Profit Growth, Debt-to-Equity, Current Ratio, Net Profit Margin.' },
  { num: '3', title: 'Prototype Risk Rules',  desc: 'Each metric is classified LOW, MODERATE, or HIGH using transparent prototype thresholds.' },
  { num: '4', title: 'Risk Indicator',        desc: 'The overall indicator is the worst (highest) signal across all five metrics.' },
  { num: '5', title: 'Explainable Results',   desc: 'Every metric, value, threshold, and classification is shown — no black boxes.' },
];

const THRESHOLDS = [
  { metric: 'Revenue Growth',    low: '≥ 10%',   moderate: '0% – 9.99%',  high: '< 0%' },
  { metric: 'Profit Growth',     low: '> 0%',    moderate: '0% to −10%',  high: '< −10%' },
  { metric: 'Debt-to-Equity',    low: '< 0.5×',  moderate: '0.5 – <1.0×', high: '≥ 1.0×' },
  { metric: 'Current Ratio',     low: '≥ 2.0×',  moderate: '1.0 – <2.0×', high: '< 1.0×' },
  { metric: 'Net Profit Margin', low: '≥ 10%',   moderate: '0% – 9.99%',  high: '< 0%' },
];

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="section">
      <div className="section-inner">
        <div className="section-label">Process</div>
        <h2 className="section-title">How It Works</h2>
        <p className="section-subtitle">
          FinRisk AI uses a fully transparent, deterministic process.
          No machine-learning model determines the metric values or overall risk classification.
        </p>

        {/* Process steps */}
        <div className="process-steps" aria-label="Five-step analysis process">
          {PROCESS_STEPS.map((step, i) => (
            <div key={step.num} style={{ display: 'contents' }}>
              <div className="process-step">
                <div className="process-step-number" aria-label={`Step ${step.num}`}>{step.num}</div>
                <div className="process-step-title">{step.title}</div>
                <div className="process-step-desc">{step.desc}</div>
              </div>
              {i < PROCESS_STEPS.length - 1 && (
                <div className="process-arrow" aria-hidden="true">→</div>
              )}
            </div>
          ))}
        </div>

        {/* Threshold reference */}
        <div className="determinism-box" style={{ background: '#fff', border: '1px solid var(--color-border)', marginTop: '36px' }}>
          <h3 style={{ color: 'var(--color-text)', marginBottom: '6px' }}>Prototype Thresholds Reference</h3>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '16px', fontStyle: 'italic' }}>
            These are prototype thresholds used for demonstration purposes only. They are not universal financial standards.
          </p>
          <div className="threshold-table-wrap">
            <table className="threshold-table">
              <thead>
                <tr>
                  <th style={{ color: 'var(--color-text-muted)' }}>Metric</th>
                  <th style={{ color: 'var(--color-low)' }}>LOW</th>
                  <th style={{ color: 'var(--color-moderate)' }}>MODERATE</th>
                  <th style={{ color: 'var(--color-high)' }}>HIGH</th>
                </tr>
              </thead>
              <tbody>
                {THRESHOLDS.map((row) => (
                  <tr key={row.metric}>
                    <td style={{ fontWeight: 600, color: 'var(--color-text)' }}>{row.metric}</td>
                    <td style={{ color: 'var(--color-low)' }}>{row.low}</td>
                    <td style={{ color: 'var(--color-moderate)' }}>{row.moderate}</td>
                    <td style={{ color: 'var(--color-high)' }}>{row.high}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="determinism-box">
          <h3>Deterministic Classification — AI for Explanation Only</h3>
          <p>
            The Prototype Financial Risk Indicator is computed entirely by deterministic arithmetic.
            No AI model calculates, adjusts, or overrides any metric value or risk classification.
            After the deterministic analysis is complete, Gemini AI is optionally called by the backend
            to generate a plain-language explanation of those already-calculated results.
            Gemini receives only the compact numeric output — it never influences the financial metrics
            or the LOW / MODERATE / HIGH classification.
            All thresholds are clearly labelled as prototype thresholds throughout the application.
          </p>
        </div>
      </div>
    </section>
  );
}

// ── Responsible AI Section ────────────────────────────────────────────────────

const RAI_PRINCIPLES = [
  { icon: '🔍', title: 'Transparency',           text: 'Every calculation, threshold, and classification is shown. There are no hidden models, no opaque scoring, and no unexplained outputs.' },
  { icon: '👤', title: 'Human Oversight',         text: 'FinRisk AI is a decision-support prototype. Financial professionals must review and validate all outputs before any decision is made.' },
  { icon: '⚖️', title: 'Fairness',                text: 'The same prototype thresholds are applied consistently to all inputs. No demographic or non-financial factors influence the classification.' },
  { icon: '🔒', title: 'Privacy',                  text: 'Financial inputs are processed by the FinRisk AI backend for calculation. When the Gemini explanation is enabled, the backend may send the compact calculated risk results to the Google Gemini API to generate an explanation. Your raw financial inputs are not forwarded. The Gemini API key is kept server-side and is never exposed to the browser.' },
  { icon: '💡', title: 'Explainability',           text: 'The results page explains which metrics contributed to the overall risk level, what each value means, and why each threshold was triggered.' },
  { icon: '📋', title: 'Accuracy and Limitations', text: 'FinRisk AI uses prototype thresholds that are not universal financial standards. Results reflect a simplified model and do not replace professional analysis.' },
  { icon: '✅', title: 'Responsible Use',           text: 'FinRisk AI is intended for educational and prototype use only. It must not be used to make investment, lending, credit, or professional financial decisions.' },
];

function ResponsibleAISection() {
  return (
    <section id="responsible-ai" className="section" style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}>
      <div className="section-inner">
        <div className="section-label">Responsible AI</div>
        <h2 className="section-title">Responsible AI Principles</h2>
        <p className="section-subtitle">
          FinRisk AI is designed to support responsible, transparent, and accountable financial decision-making.
        </p>

        <div className="rai-grid">
          {RAI_PRINCIPLES.map((p) => (
            <div key={p.title} className="rai-card">
              <div className="rai-card-icon" aria-hidden="true">{p.icon}</div>
              <div className="rai-card-title">{p.title}</div>
              <div className="rai-card-text">{p.text}</div>
            </div>
          ))}
        </div>

        <div className="disclaimer-box">
          <h3>Important Disclaimer</h3>
          <p>
            FinRisk AI is a prototype decision-support system and does not provide investment,
            lending, credit, tax, or professional financial advice. All outputs are based on
            prototype thresholds that are not universal financial standards. Always consult a
            qualified financial professional before making any financial decisions.
          </p>
        </div>
      </div>
    </section>
  );
}

// ── SDG 12 Section ────────────────────────────────────────────────────────────

function SDG12Section() {
  return (
    <section id="sdg12" className="section">
      <div className="section-inner">
        <div className="section-label">UN Sustainable Development Goals</div>
        <h2 className="section-title">SDG 12 — Responsible Consumption and Production</h2>
        <p className="section-subtitle" style={{ marginBottom: '28px' }}>
          How FinRisk AI supports more responsible and informed financial decision-making.
        </p>

        <div className="sdg-card">
          <div className="sdg-number" aria-label="SDG Goal 12">12</div>
          <div className="sdg-sdg-label">Sustainable Development Goal</div>
          <div className="sdg-title">Responsible Consumption and Production</div>

          <p className="sdg-body">
            UN Sustainable Development Goal 12 calls for responsible management of natural and
            financial resources, sustainable business practices, and informed decision-making
            that reduces waste and improves economic sustainability.
          </p>
          <p className="sdg-body">
            FinRisk AI supports this goal by enabling more informed and responsible use of financial
            resources. By providing transparent, explainable financial risk indicators, FinRisk AI
            helps businesses, educators, and analysts make more considered financial decisions —
            reducing the risk of misallocated capital, unsustainable debt, and uninformed choices.
          </p>
          <p className="sdg-body">Better financial risk awareness supports:</p>
          <ul className="sdg-list" aria-label="Benefits of financial risk awareness">
            <li>More sustainable allocation of financial resources</li>
            <li>Reduced risk of corporate insolvency and economic disruption</li>
            <li>Increased financial literacy and responsible financial planning</li>
            <li>More transparent decision-making for business stakeholders</li>
          </ul>
          <div className="sdg-caveat">
            <strong>Scope caveat:</strong> FinRisk AI does not directly solve SDG 12 and makes no
            such claim. It is a prototype educational tool that supports more responsible and
            transparent financial decision-making within its limited scope. Its contribution to
            SDG 12 is indirect and educational in nature.
          </div>
        </div>
      </div>
    </section>
  );
}

// ── About Section ─────────────────────────────────────────────────────────────

const FUTURE_FEATURES = [
  'IBM Granite / watsonx.ai as an alternative or additional AI explanation provider',
  'Financial document analysis (PDF/DOCX balance sheets)',
  'Retrieval-Augmented Generation (RAG) for financial intelligence',
  'Anomaly detection in multi-period financial data',
  'Historical trend analysis across multiple periods',
  'Financial entity extraction and relationship mapping',
  'Continuous financial monitoring and alerts',
  'Covenant monitoring for lending compliance',
  'Integration with financial intelligence APIs',
];

function AboutSection() {
  return (
    <section id="about" className="section" style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}>
      <div className="section-inner">
        <div className="section-label">About</div>
        <h2 className="section-title">About FinRisk AI</h2>

        <div className="about-grid">
          <div>
            <div className="about-section-title">What is FinRisk AI?</div>
            <p className="about-body">
              FinRisk AI is a prototype financial risk decision-support system demonstrating transparent,
              explainable financial analysis. It accepts nine basic financial inputs and produces a
              structured Prototype Financial Risk Indicator using five core financial metrics.
            </p>

            <div className="about-section-title">Purpose</div>
            <p className="about-body">
              Built as an internship MVP to demonstrate responsible AI principles in a financial context:
              deterministic calculations, transparent thresholds, explainable results, and clear
              human-oversight positioning.
            </p>

            <div className="about-section-title">Intended Use</div>
            <p className="about-body">
              FinRisk AI is intended for educational, demonstration, and prototype purposes only.
              It is not suitable for production financial analysis, investment decisions, lending
              assessments, credit scoring, or any regulated financial activity.
            </p>

            <div className="about-section-title">Responsible AI Approach</div>
            <p className="about-body">
              All metric calculations are deterministic — the same inputs always produce the same outputs.
              No AI model calculates, modifies, or overrides any metric value or risk classification.
              Gemini AI is used separately by the backend to generate an optional plain-language explanation
              of the already-calculated results; it does not influence the financial metrics or the
              Prototype Financial Risk Indicator.
              Thresholds are clearly labelled as prototype thresholds throughout the application.
            </p>

            <div className="about-section-title">Prototype Limitations</div>
            <p className="about-body">
              The prototype thresholds are simplified approximations and not universal financial standards.
              They do not account for industry sector, geography, company size, economic cycle, or other
              contextual factors that professional analysts would consider.
            </p>
          </div>

          <div>
            <div className="future-card">
              <div className="future-card-title">
                <span aria-hidden="true">🔭</span> Future Scope
              </div>
              <div className="future-not-impl">Not yet implemented</div>
              <p style={{ fontSize: '12.5px', color: 'var(--color-text-muted)', marginBottom: '14px', lineHeight: '1.6' }}>
                The current MVP includes deterministic financial analysis and optional Gemini AI explanations.
                The following features may be added in future versions.
              </p>
              {FUTURE_FEATURES.map((f) => (
                <div key={f} className="future-item">
                  <div className="future-item-dot" aria-hidden="true" />
                  <span>{f}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────────

function Footer({ onNav }) {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">FinRisk AI</div>
        <div className="footer-tagline">Prototype Financial Risk Decision-Support System</div>
        <div className="footer-disclaimer">
          FinRisk AI is a prototype decision-support system and does not provide investment,
          lending, credit, tax, or professional financial advice. All thresholds are prototype
          thresholds and are not universal financial standards.
        </div>
        <nav className="footer-links" aria-label="Footer navigation">
          {[
            ['home',           'Home'],
            ['analyze',        'Analyze'],
            ['how-it-works',   'How It Works'],
            ['responsible-ai', 'Responsible AI'],
            ['sdg12',          'SDG 12'],
            ['about',          'About'],
          ].map(([id, label]) => (
            <button key={id} className="footer-link-btn" onClick={() => onNav(id)}>
              {label}
            </button>
          ))}
        </nav>
      </div>
    </footer>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [activeSection, setActiveSection] = useState('home');
  const [results, setResults] = useState(null);
  const [isDemo, setIsDemo] = useState(false);
  const [isDemoLoaded, setIsDemoLoaded] = useState(false);

  const scrollToSection = useCallback((id) => {
    setActiveSection(id);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  const handleResults = useCallback((result, demo) => {
    setResults(result);
    setIsDemo(demo);
    setActiveSection('results');
    setTimeout(() => {
      const el = document.getElementById('results');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
  }, []);

  const handleNewAnalysis = useCallback(() => scrollToSection('analyze'), [scrollToSection]);
  const handleStartAnalysis = useCallback(() => scrollToSection('analyze'), [scrollToSection]);

  return (
    <div>
      <Nav
        activeSection={activeSection}
        onNav={scrollToSection}
        onStartAnalysis={handleStartAnalysis}
      />
      <main>
        <HomeSection onStartAnalysis={handleStartAnalysis} onNav={scrollToSection} />
        <AnalyzeSection
          onResults={handleResults}
          isDemoLoaded={isDemoLoaded}
          setIsDemoLoaded={setIsDemoLoaded}
        />
        <ResultsSection result={results} isDemo={isDemo} onNewAnalysis={handleNewAnalysis} />
        <HowItWorksSection />
        <ResponsibleAISection />
        <SDG12Section />
        <AboutSection />
      </main>
      <Footer onNav={scrollToSection} />
    </div>
  );
}
