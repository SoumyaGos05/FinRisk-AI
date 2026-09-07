"""
Prototype Financial Risk Indicator — deterministic calculation engine.

All five metrics and the overall risk classification are computed here using
pure Python arithmetic.  No AI, no ML model, and no external service ever
touches these values.

Prototype Thresholds (not universal financial standards)
---------------------------------------------------------
Revenue Growth (% YoY):
    HIGH_GROWTH    >= 10%     → LOW concern
    MODERATE_GROWTH 0–9.99%  → MODERATE concern
    DECLINING      < 0%       → HIGH concern

Profit Growth (% YoY):
    POSITIVE       > 0%       → LOW concern
    MODERATE_DECLINE 0 to -10%→ MODERATE concern
    HIGH_DECLINE   < -10%     → HIGH concern

Debt-to-Equity ratio:
    LOW            < 0.5      → LOW concern
    MODERATE       0.5–<1.0   → MODERATE concern
    HIGH           1.0–<2.0   → HIGH concern
    VERY_HIGH      >= 2.0     → HIGH concern (treated as HIGH)

Current Ratio:
    STRONG         >= 2.0     → LOW concern
    NORMAL         1.0–<2.0   → MODERATE concern
    LIQUIDITY      < 1.0      → HIGH concern

Net Profit Margin (% of revenue):
    HEALTHY        >= 10%     → LOW concern
    MODERATE_MG    5–<10%     → MODERATE concern
    LOW_MG         0–<5%      → MODERATE concern (borderline)
    NEGATIVE_MG    < 0%       → HIGH concern

Overall Prototype Financial Risk Indicator = worst (highest) signal across
all five metrics, resolved as: LOW → MODERATE → HIGH.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

RiskLevel = Literal["LOW", "MODERATE", "HIGH"]

_LEVEL_ORDER: dict[str, int] = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
_LEVEL_FROM_ORDER: dict[int, str] = {v: k for k, v in _LEVEL_ORDER.items()}

# ---------------------------------------------------------------------------
# Thresholds (prototype — not universal financial standards)
# ---------------------------------------------------------------------------

# Revenue growth (%)
_REV_GROWTH_LOW_THRESHOLD: float = 10.0   # >= 10% → LOW
_REV_GROWTH_MOD_THRESHOLD: float = 0.0    # 0–<10% → MODERATE, <0% → HIGH

# Profit growth (%)
_PROFIT_GROWTH_LOW_THRESHOLD: float = 0.0    # > 0 → LOW
_PROFIT_GROWTH_MOD_THRESHOLD: float = -10.0  # -10–0 → MODERATE, < -10 → HIGH

# Debt-to-Equity
_DTE_LOW: float = 0.5
_DTE_MOD: float = 1.0
_DTE_HIGH: float = 2.0

# Current ratio
_CR_STRONG: float = 2.0
_CR_NORMAL: float = 1.0

# Net profit margin (%)
_NPM_HEALTHY: float = 10.0
_NPM_MODERATE: float = 5.0
_NPM_LOW: float = 0.0


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class MetricResult:
    """Single metric value with its prototype risk classification."""

    name: str
    value: float
    formatted_value: str
    level: RiskLevel
    explanation: str
    threshold_note: str


@dataclass
class FinancialRiskResult:
    """Complete result of the prototype financial risk analysis."""

    company_name: str
    overall_risk: RiskLevel
    overall_explanation: str
    metrics: list[MetricResult] = field(default_factory=list)
    # Raw inputs stored for trend display
    current_revenue: float = 0.0
    previous_revenue: float = 0.0
    current_net_profit: float = 0.0
    previous_net_profit: float = 0.0


# ---------------------------------------------------------------------------
# Individual metric calculators
# ---------------------------------------------------------------------------


def calculate_revenue_growth(current: float, previous: float) -> float:
    """
    Revenue Growth = (current - previous) / previous × 100.

    Raises:
        ValueError: If previous revenue is zero.
    """
    if previous == 0.0:
        raise ValueError("Previous revenue must not be zero.")
    return (current - previous) / previous * 100.0


def calculate_profit_growth(current: float, previous: float) -> float:
    """
    Profit Growth = (current - previous) / previous × 100.

    Raises:
        ValueError: If previous net profit is zero.
    """
    if previous == 0.0:
        raise ValueError("Previous net profit must not be zero.")
    return (current - previous) / previous * 100.0


def calculate_debt_to_equity(total_debt: float, shareholders_equity: float) -> float:
    """
    Debt-to-Equity = total_debt / shareholders_equity.

    Raises:
        ValueError: If shareholders' equity is zero.
    """
    if shareholders_equity == 0.0:
        raise ValueError("Shareholders' equity must not be zero.")
    return total_debt / shareholders_equity


def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
    """
    Current Ratio = current_assets / current_liabilities.

    Raises:
        ValueError: If current liabilities are zero.
    """
    if current_liabilities == 0.0:
        raise ValueError("Current liabilities must not be zero.")
    return current_assets / current_liabilities


def calculate_net_profit_margin(net_profit: float, revenue: float) -> float:
    """
    Net Profit Margin = net_profit / revenue × 100.

    Raises:
        ValueError: If revenue is zero.
    """
    if revenue == 0.0:
        raise ValueError("Current revenue must not be zero.")
    return net_profit / revenue * 100.0


# ---------------------------------------------------------------------------
# Classifiers
# ---------------------------------------------------------------------------


def _classify_revenue_growth(pct: float) -> tuple[RiskLevel, str]:
    if pct >= _REV_GROWTH_LOW_THRESHOLD:
        return "LOW", f"Revenue grew by {pct:.1f}%, indicating healthy expansion."
    if pct >= _REV_GROWTH_MOD_THRESHOLD:
        return "MODERATE", f"Revenue grew by {pct:.1f}%, showing slow or flat growth."
    return "HIGH", f"Revenue declined by {abs(pct):.1f}%, a warning sign for the business."


def _classify_profit_growth(pct: float) -> tuple[RiskLevel, str]:
    if pct > _PROFIT_GROWTH_LOW_THRESHOLD:
        return "LOW", f"Net profit grew by {pct:.1f}%, a positive indicator."
    if pct >= _PROFIT_GROWTH_MOD_THRESHOLD:
        return "MODERATE", f"Net profit changed by {pct:.1f}%, a moderate concern."
    return "HIGH", f"Net profit declined by {abs(pct):.1f}%, exceeding the -10% concern threshold."


def _classify_debt_to_equity(dte: float) -> tuple[RiskLevel, str]:
    if dte < _DTE_LOW:
        return "LOW", f"Debt-to-Equity of {dte:.2f} indicates low financial leverage."
    if dte < _DTE_MOD:
        return "MODERATE", f"Debt-to-Equity of {dte:.2f} indicates moderate leverage."
    if dte < _DTE_HIGH:
        return "HIGH", f"Debt-to-Equity of {dte:.2f} indicates high leverage."
    return "HIGH", f"Debt-to-Equity of {dte:.2f} indicates very high leverage, a significant risk."


def _classify_current_ratio(cr: float) -> tuple[RiskLevel, str]:
    if cr >= _CR_STRONG:
        return "LOW", f"Current Ratio of {cr:.2f} shows strong short-term liquidity."
    if cr >= _CR_NORMAL:
        return "MODERATE", f"Current Ratio of {cr:.2f} is within normal range."
    return "HIGH", f"Current Ratio of {cr:.2f} signals a potential liquidity concern."


def _classify_net_profit_margin(npm: float) -> tuple[RiskLevel, str]:
    if npm >= _NPM_HEALTHY:
        return "LOW", f"Net Profit Margin of {npm:.1f}% is healthy."
    if npm >= _NPM_MODERATE:
        return "MODERATE", f"Net Profit Margin of {npm:.1f}% is acceptable but below ideal."
    if npm >= _NPM_LOW:
        return "MODERATE", f"Net Profit Margin of {npm:.1f}% is low; profitability is thin."
    return "HIGH", f"Net Profit Margin of {npm:.1f}% is negative; the company is loss-making."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyse_financial_risk(
    company_name: str,
    current_revenue: float,
    previous_revenue: float,
    current_net_profit: float,
    previous_net_profit: float,
    total_debt: float,
    shareholders_equity: float,
    current_assets: float,
    current_liabilities: float,
) -> FinancialRiskResult:
    """
    Compute the Prototype Financial Risk Indicator for a company.

    All five metrics are calculated deterministically from the inputs.
    The overall risk level is the worst (highest) individual signal.

    Args:
        company_name:         Name of the company being analysed.
        current_revenue:      Most recent period revenue.
        previous_revenue:     Prior period revenue (must not be zero).
        current_net_profit:   Most recent period net profit.
        previous_net_profit:  Prior period net profit (must not be zero).
        total_debt:           Total outstanding debt.
        shareholders_equity:  Total shareholders' equity (must not be zero).
        current_assets:       Total current assets.
        current_liabilities:  Total current liabilities (must not be zero).

    Returns:
        A :class:`FinancialRiskResult` with all metrics and the overall indicator.

    Raises:
        ValueError: If any denominator input is zero.
    """
    rev_growth = calculate_revenue_growth(current_revenue, previous_revenue)
    profit_growth = calculate_profit_growth(current_net_profit, previous_net_profit)
    dte = calculate_debt_to_equity(total_debt, shareholders_equity)
    cr = calculate_current_ratio(current_assets, current_liabilities)
    npm = calculate_net_profit_margin(current_net_profit, current_revenue)

    rev_level, rev_msg = _classify_revenue_growth(rev_growth)
    profit_level, profit_msg = _classify_profit_growth(profit_growth)
    dte_level, dte_msg = _classify_debt_to_equity(dte)
    cr_level, cr_msg = _classify_current_ratio(cr)
    npm_level, npm_msg = _classify_net_profit_margin(npm)

    worst = max(
        _LEVEL_ORDER[rev_level],
        _LEVEL_ORDER[profit_level],
        _LEVEL_ORDER[dte_level],
        _LEVEL_ORDER[cr_level],
        _LEVEL_ORDER[npm_level],
    )
    overall: RiskLevel = _LEVEL_FROM_ORDER[worst]  # type: ignore[assignment]

    overall_texts = {
        "LOW": "Overall financial indicators suggest low risk. The company shows sound fundamentals across most metrics.",
        "MODERATE": "Some financial metrics fall within moderate-concern ranges. Careful monitoring is advised.",
        "HIGH": "One or more financial metrics indicate high concern. This warrants detailed professional review.",
    }

    metrics = [
        MetricResult(
            name="Revenue Growth",
            value=round(rev_growth, 2),
            formatted_value=f"{rev_growth:.1f}%",
            level=rev_level,
            explanation=rev_msg,
            threshold_note="Prototype thresholds: ≥10% = LOW, 0–<10% = MODERATE, <0% = HIGH",
        ),
        MetricResult(
            name="Profit Growth",
            value=round(profit_growth, 2),
            formatted_value=f"{profit_growth:.1f}%",
            level=profit_level,
            explanation=profit_msg,
            threshold_note="Prototype thresholds: >0% = LOW, 0 to -10% = MODERATE, <-10% = HIGH",
        ),
        MetricResult(
            name="Debt-to-Equity",
            value=round(dte, 4),
            formatted_value=f"{dte:.2f}x",
            level=dte_level,
            explanation=dte_msg,
            threshold_note="Prototype thresholds: <0.5 = LOW, 0.5–<1 = MODERATE, 1–<2 = HIGH, ≥2 = HIGH (very high)",
        ),
        MetricResult(
            name="Current Ratio",
            value=round(cr, 4),
            formatted_value=f"{cr:.2f}x",
            level=cr_level,
            explanation=cr_msg,
            threshold_note="Prototype thresholds: ≥2 = LOW (strong), 1–<2 = MODERATE (normal), <1 = HIGH (liquidity concern)",
        ),
        MetricResult(
            name="Net Profit Margin",
            value=round(npm, 2),
            formatted_value=f"{npm:.1f}%",
            level=npm_level,
            explanation=npm_msg,
            threshold_note="Prototype thresholds: ≥10% = LOW, 5–<10% = MODERATE, 0–<5% = MODERATE (low), <0% = HIGH",
        ),
    ]

    return FinancialRiskResult(
        company_name=company_name,
        overall_risk=overall,
        overall_explanation=overall_texts[overall],
        metrics=metrics,
        current_revenue=current_revenue,
        previous_revenue=previous_revenue,
        current_net_profit=current_net_profit,
        previous_net_profit=previous_net_profit,
    )
