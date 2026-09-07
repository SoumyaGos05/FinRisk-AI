"""
Explainable Risk Recommendation Layer.

Pure-Python, rule-based module that translates the four core risk metrics
(volatility, VaR, Sharpe ratio, max drawdown) into a human-readable risk
level, a single action-oriented recommendation, and a short list of
explanation flags that justify the assessment.

No FastAPI, no database, no HTTP calls, no external dependencies.
All logic is deterministic: identical inputs always produce identical outputs.

Thresholds
----------
Volatility (annualised):
    LOW       < 0.15  (< 15%)
    MODERATE  0.15 – 0.30
    HIGH      > 0.30  (> 30%)

VaR (as a fraction of portfolio value, i.e. ``var / portfolio_value``):
    LOW       < 0.02  (< 2%)
    MODERATE  0.02 – 0.05
    HIGH      > 0.05  (> 5%)

Sharpe ratio:
    HIGH (good)     > 1.0
    MODERATE        0.5 – 1.0
    LOW (poor)      < 0.5   (or negative)

Max drawdown:
    LOW       < 0.10  (< 10%)
    MODERATE  0.10 – 0.25
    HIGH      > 0.25  (> 25%)

Overall risk level is the *worst* (highest) individual signal across all four
metrics so that a single alarming metric cannot be hidden by three good ones.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Thresholds (module-level constants for easy future tuning)
# ---------------------------------------------------------------------------

# Volatility (annualised, decimal)
_VOL_LOW: float = 0.15
_VOL_HIGH: float = 0.30

# VaR expressed as a fraction of portfolio_value
_VAR_LOW: float = 0.02
_VAR_HIGH: float = 0.05

# Sharpe ratio (higher is better)
_SHARPE_GOOD: float = 1.0
_SHARPE_MODERATE: float = 0.5

# Max drawdown (decimal)
_DD_LOW: float = 0.10
_DD_HIGH: float = 0.25

# Ordered severity so we can take max(signals)
_LEVEL_ORDER: dict[str, int] = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
_LEVEL_FROM_ORDER: dict[int, str] = {v: k for k, v in _LEVEL_ORDER.items()}

RiskLevel = Literal["LOW", "MODERATE", "HIGH"]

# ---------------------------------------------------------------------------
# Pydantic output schema (kept here alongside the logic it describes)
# ---------------------------------------------------------------------------


class RiskRecommendation(BaseModel):
    """Explainable risk recommendation derived from the four core metrics."""

    risk_level: RiskLevel = Field(
        ...,
        description="Overall risk classification: LOW, MODERATE, or HIGH.",
    )
    recommendation: str = Field(
        ...,
        description="One concise action-oriented message for the investor.",
    )
    explanations: list[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2–4 flags explaining why this risk level was assigned.",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _classify_volatility(volatility: float) -> tuple[str, str]:
    """Return (level, explanation) for the volatility metric."""
    pct = volatility * 100
    if volatility < _VOL_LOW:
        return "LOW", f"Annualised volatility is low at {pct:.1f}%."
    if volatility <= _VOL_HIGH:
        return "MODERATE", f"Annualised volatility is moderate at {pct:.1f}%."
    return "HIGH", f"Annualised volatility is high at {pct:.1f}%."


def _classify_var(var: float, portfolio_value: float) -> tuple[str, str]:
    """Return (level, explanation) for the VaR metric."""
    fraction = var / portfolio_value if portfolio_value > 0 else var
    pct = fraction * 100
    if fraction < _VAR_LOW:
        return "LOW", f"Value-at-Risk is low ({pct:.2f}% of portfolio per day)."
    if fraction <= _VAR_HIGH:
        return "MODERATE", f"Value-at-Risk is moderate ({pct:.2f}% of portfolio per day)."
    return "HIGH", f"Value-at-Risk is high ({pct:.2f}% of portfolio per day)."


def _classify_sharpe(sharpe: float) -> tuple[str, str]:
    """Return (level, explanation) for the Sharpe ratio metric.

    Note: a *good* Sharpe maps to a *low* risk level and vice-versa.
    """
    if sharpe >= _SHARPE_GOOD:
        return "LOW", f"Sharpe ratio is strong at {sharpe:.2f}, indicating good risk-adjusted returns."
    if sharpe >= _SHARPE_MODERATE:
        return "MODERATE", f"Sharpe ratio is acceptable at {sharpe:.2f}."
    return "HIGH", f"Sharpe ratio is weak at {sharpe:.2f}, suggesting poor risk-adjusted returns."


def _classify_drawdown(max_drawdown: float) -> tuple[str, str]:
    """Return (level, explanation) for the max-drawdown metric."""
    pct = max_drawdown * 100
    if max_drawdown < _DD_LOW:
        return "LOW", f"Maximum drawdown is small at {pct:.1f}%."
    if max_drawdown <= _DD_HIGH:
        return "MODERATE", f"Maximum drawdown is moderate at {pct:.1f}%."
    return "HIGH", f"Maximum drawdown is severe at {pct:.1f}%."


_RECOMMENDATIONS: dict[str, str] = {
    "LOW": (
        "This asset shows low risk characteristics. "
        "It may be suitable for conservative investors; continue monitoring for changes."
    ),
    "MODERATE": (
        "This asset carries moderate risk. "
        "Ensure position sizing aligns with your risk tolerance and review periodically."
    ),
    "HIGH": (
        "This asset exhibits high risk. "
        "Consider reducing exposure, diversifying, or applying stop-loss controls."
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_recommendation(
    volatility: float,
    var: float,
    sharpe_ratio: float,
    max_drawdown: float,
    portfolio_value: float = 1.0,
) -> RiskRecommendation:
    """
    Derive a risk level, recommendation, and explanation flags from risk metrics.

    Args:
        volatility:     Annualised volatility (decimal, e.g. 0.20 for 20%).
        var:            Parametric VaR in the same units as *portfolio_value*.
        sharpe_ratio:   Annualised Sharpe ratio (dimensionless).
        max_drawdown:   Maximum peak-to-trough drawdown (decimal, e.g. 0.15).
        portfolio_value: Portfolio value used to normalise VaR. Defaults to 1.0.

    Returns:
        A :class:`RiskRecommendation` with ``risk_level``, ``recommendation``,
        and ``explanations``.
    """
    vol_level, vol_msg = _classify_volatility(volatility)
    var_level, var_msg = _classify_var(var, portfolio_value)
    sharpe_level, sharpe_msg = _classify_sharpe(sharpe_ratio)
    dd_level, dd_msg = _classify_drawdown(max_drawdown)

    # Overall level = worst individual signal
    worst = max(
        _LEVEL_ORDER[vol_level],
        _LEVEL_ORDER[var_level],
        _LEVEL_ORDER[sharpe_level],
        _LEVEL_ORDER[dd_level],
    )
    overall: RiskLevel = _LEVEL_FROM_ORDER[worst]  # type: ignore[assignment]

    return RiskRecommendation(
        risk_level=overall,
        recommendation=_RECOMMENDATIONS[overall],
        explanations=[vol_msg, var_msg, sharpe_msg, dd_msg],
    )
