/**
 * RiskDashboard component.
 *
 * Lets the user enter a stock ticker and select a period, then calls the
 * POST /risk/analyse/ticker API and displays the returned risk metrics.
 */

import { useState } from 'react';
import { apiBase } from '../api.js';
import './RiskDashboard.css';

const PERIODS = [
  { value: '1mo', label: '1 Month' },
  { value: '3mo', label: '3 Months' },
  { value: '6mo', label: '6 Months' },
  { value: '1y',  label: '1 Year' },
  { value: '2y',  label: '2 Years' },
  { value: '5y',  label: '5 Years' },
  { value: 'ytd', label: 'Year to Date' },
  { value: 'max', label: 'Max' },
];

/**
 * Format a decimal as a percentage string, e.g. 0.1523 → "15.23%"
 * @param {number} value
 * @returns {string}
 */
function formatPercent(value) {
  return (value * 100).toFixed(2) + '%';
}

/**
 * Format a plain float to 4 decimal places.
 * @param {number} value
 * @returns {string}
 */
function formatDecimal(value) {
  return value.toFixed(4);
}

/**
 * A single metric card inside the results grid.
 * @param {{ label: string, value: string, description: string }} props
 */
function MetricCard({ label, value, description }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-description">{description}</div>
    </div>
  );
}

/**
 * Main Risk Dashboard component.
 */
function RiskDashboard() {
  const [ticker, setTicker] = useState('');
  const [period, setPeriod] = useState('1y');
  const [tickerError, setTickerError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [result, setResult] = useState(null);

  /**
   * Validate the ticker field. Returns an error string or empty string.
   * @param {string} value
   * @returns {string}
   */
  function validateTicker(value) {
    const trimmed = value.trim();
    if (!trimmed) return 'Please enter a stock ticker symbol.';
    if (trimmed.length > 20) return 'Ticker must be at most 20 characters.';
    if (!/^[A-Za-z0-9.^-]+$/.test(trimmed)) return 'Ticker contains invalid characters.';
    return '';
  }

  /**
   * Handle ticker input changes — clear stale results and validate on the fly.
   * @param {React.ChangeEvent<HTMLInputElement>} e
   */
  function handleTickerChange(e) {
    const value = e.target.value;
    setTicker(value);
    setTickerError(validateTicker(value));
    if (result) setResult(null);
    if (apiError) setApiError('');
  }

  /**
   * Handle period select changes — clear stale results.
   * @param {React.ChangeEvent<HTMLSelectElement>} e
   */
  function handlePeriodChange(e) {
    setPeriod(e.target.value);
    if (result) setResult(null);
    if (apiError) setApiError('');
  }

  /**
   * Submit the form: validate, call the API, update state.
   * @param {React.FormEvent<HTMLFormElement>} e
   */
  async function handleSubmit(e) {
    e.preventDefault();

    const error = validateTicker(ticker);
    if (error) {
      setTickerError(error);
      return;
    }

    setTickerError('');
    setApiError('');
    setResult(null);
    setLoading(true);

    try {
      const response = await fetch(`${apiBase}/risk/analyse/ticker`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: ticker.trim().toUpperCase(), period }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail ?? `Request failed (HTTP ${response.status}).`;
        setApiError(typeof detail === 'string' ? detail : JSON.stringify(detail));
        return;
      }

      const data = await response.json();
      setResult(data);
    } catch {
      setApiError('Could not reach the API. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  const isSubmitDisabled = loading || !!validateTicker(ticker);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1 className="dashboard-title">FinRisk AI</h1>
        <p className="dashboard-subtitle">Financial risk analysis for any publicly traded stock.</p>
      </header>

      <main className="dashboard-main">
        <form className="analysis-form" onSubmit={handleSubmit} noValidate>
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="ticker-input" className="form-label">Ticker Symbol</label>
              <input
                id="ticker-input"
                className={`form-input${tickerError ? ' form-input--error' : ''}`}
                type="text"
                value={ticker}
                onChange={handleTickerChange}
                placeholder="e.g. AAPL"
                maxLength={20}
                autoComplete="off"
                spellCheck={false}
                aria-describedby={tickerError ? 'ticker-error' : undefined}
                aria-invalid={!!tickerError}
              />
              {tickerError && (
                <span id="ticker-error" className="field-error" role="alert">{tickerError}</span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="period-select" className="form-label">Period</label>
              <select
                id="period-select"
                className="form-select"
                value={period}
                onChange={handlePeriodChange}
              >
                {PERIODS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div className="form-field form-field--action">
              <button
                type="submit"
                className="submit-btn"
                disabled={isSubmitDisabled}
                aria-busy={loading}
              >
                {loading ? 'Analysing…' : 'Analyse Risk'}
              </button>
            </div>
          </div>
        </form>

        {apiError && (
          <div className="api-error" role="alert">
            <strong>Error:</strong> {apiError}
          </div>
        )}

        {loading && (
          <div className="loading-state" aria-live="polite">
            <div className="spinner" aria-hidden="true" />
            <span>Fetching market data and computing risk metrics…</span>
          </div>
        )}

        {result && !loading && (
          <section className="results" aria-label="Risk analysis results">
            <div className="results-header">
              <h2 className="results-ticker">{result.ticker}</h2>
              <span className="results-period">{result.period_used}</span>
            </div>
            <div className="metrics-grid">
              <MetricCard
                label="Annualised Volatility"
                value={formatPercent(result.volatility)}
                description="Standard deviation of daily returns, scaled to one year."
              />
              <MetricCard
                label="Value at Risk (95%)"
                value={formatDecimal(result.var)}
                description="Estimated maximum loss per unit of portfolio value at 95% confidence."
              />
              <MetricCard
                label="Sharpe Ratio"
                value={formatDecimal(result.sharpe_ratio)}
                description="Annualised excess return per unit of risk (risk-free rate = 0%)."
              />
              <MetricCard
                label="Maximum Drawdown"
                value={formatPercent(result.max_drawdown)}
                description="Largest peak-to-trough decline over the selected period."
              />
              <MetricCard
                label="Data Points"
                value={result.num_prices.toLocaleString()}
                description="Number of daily closing prices used in the analysis."
              />
            </div>

            {result.recommendation && (
              <div className={`recommendation recommendation--${result.recommendation.risk_level.toLowerCase()}`}>
                <div className="recommendation-header">
                  <span className="recommendation-level">{result.recommendation.risk_level} RISK</span>
                  <p className="recommendation-text">{result.recommendation.recommendation}</p>
                </div>
                <ul className="recommendation-explanations">
                  {result.recommendation.explanations.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default RiskDashboard;
