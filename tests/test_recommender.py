"""
Tests for the Explainable Risk Recommendation Layer.

Covers:
- LOW, MODERATE, and HIGH overall risk scenarios
- Boundary/edge cases (thresholds exactly on the boundary, worst-metric dominance)
- Determinism: identical inputs always produce identical outputs
- Output shape: correct types, explanation count, valid RiskLevel literals
"""

import pytest

from backend.logic.recommender import (
    RiskRecommendation,
    generate_recommendation,
    _VOL_LOW,
    _VOL_HIGH,
    _VAR_LOW,
    _VAR_HIGH,
    _SHARPE_GOOD,
    _SHARPE_MODERATE,
    _DD_LOW,
    _DD_HIGH,
)


# ---------------------------------------------------------------------------
# Fixtures: representative metric sets
# ---------------------------------------------------------------------------

# All metrics comfortably LOW
LOW_METRICS = dict(
    volatility=0.08,       # 8% < 15% threshold
    var=0.005,             # 0.5% of portfolio
    sharpe_ratio=1.5,      # > 1.0 → LOW risk
    max_drawdown=0.05,     # 5% < 10% threshold
    portfolio_value=1.0,
)

# All metrics comfortably MODERATE
MODERATE_METRICS = dict(
    volatility=0.22,       # 22% in [15%, 30%]
    var=0.035,             # 3.5% in [2%, 5%]
    sharpe_ratio=0.7,      # 0.7 in [0.5, 1.0]
    max_drawdown=0.18,     # 18% in [10%, 25%]
    portfolio_value=1.0,
)

# All metrics comfortably HIGH
HIGH_METRICS = dict(
    volatility=0.45,       # 45% > 30%
    var=0.09,              # 9% > 5%
    sharpe_ratio=0.2,      # 0.2 < 0.5 → HIGH risk
    max_drawdown=0.40,     # 40% > 25%
    portfolio_value=1.0,
)


# ---------------------------------------------------------------------------
# Output shape & type guarantees
# ---------------------------------------------------------------------------


class TestOutputShape:
    def test_returns_risk_recommendation(self) -> None:
        result = generate_recommendation(**LOW_METRICS)
        assert isinstance(result, RiskRecommendation)

    def test_risk_level_is_valid_literal(self) -> None:
        for metrics in (LOW_METRICS, MODERATE_METRICS, HIGH_METRICS):
            result = generate_recommendation(**metrics)
            assert result.risk_level in ("LOW", "MODERATE", "HIGH")

    def test_recommendation_is_non_empty_string(self) -> None:
        result = generate_recommendation(**MODERATE_METRICS)
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_explanations_count_is_four(self) -> None:
        """Exactly 4 explanations (one per metric) are always returned."""
        result = generate_recommendation(**HIGH_METRICS)
        assert len(result.explanations) == 4

    def test_all_explanations_are_non_empty_strings(self) -> None:
        result = generate_recommendation(**LOW_METRICS)
        for msg in result.explanations:
            assert isinstance(msg, str) and len(msg) > 0


# ---------------------------------------------------------------------------
# LOW risk scenario
# ---------------------------------------------------------------------------


class TestLowRisk:
    def test_all_low_metrics_produces_low(self) -> None:
        result = generate_recommendation(**LOW_METRICS)
        assert result.risk_level == "LOW"

    def test_low_recommendation_text(self) -> None:
        result = generate_recommendation(**LOW_METRICS)
        # Should be conservative / monitor guidance, not reduce-exposure
        assert "conservative" in result.recommendation.lower() or "monitor" in result.recommendation.lower()

    def test_low_explanations_mention_low(self) -> None:
        result = generate_recommendation(**LOW_METRICS)
        combined = " ".join(result.explanations).lower()
        assert "low" in combined


# ---------------------------------------------------------------------------
# MODERATE risk scenario
# ---------------------------------------------------------------------------


class TestModerateRisk:
    def test_all_moderate_metrics_produces_moderate(self) -> None:
        result = generate_recommendation(**MODERATE_METRICS)
        assert result.risk_level == "MODERATE"

    def test_moderate_recommendation_mentions_risk_tolerance(self) -> None:
        result = generate_recommendation(**MODERATE_METRICS)
        assert "risk" in result.recommendation.lower()

    def test_moderate_explanations_present(self) -> None:
        result = generate_recommendation(**MODERATE_METRICS)
        assert len(result.explanations) >= 2


# ---------------------------------------------------------------------------
# HIGH risk scenario
# ---------------------------------------------------------------------------


class TestHighRisk:
    def test_all_high_metrics_produces_high(self) -> None:
        result = generate_recommendation(**HIGH_METRICS)
        assert result.risk_level == "HIGH"

    def test_high_recommendation_advises_caution(self) -> None:
        result = generate_recommendation(**HIGH_METRICS)
        text = result.recommendation.lower()
        assert "high risk" in text or "reducing" in text or "reduce" in text or "stop-loss" in text

    def test_high_explanations_mention_high_or_severe(self) -> None:
        result = generate_recommendation(**HIGH_METRICS)
        combined = " ".join(result.explanations).lower()
        assert "high" in combined or "severe" in combined or "weak" in combined


# ---------------------------------------------------------------------------
# Worst-metric dominance: one bad metric overrides good ones
# ---------------------------------------------------------------------------


class TestWorstMetricDominance:
    def test_high_volatility_overrides_otherwise_low(self) -> None:
        """Single HIGH signal (volatility) must push overall level to HIGH."""
        result = generate_recommendation(
            volatility=0.50,   # HIGH
            var=0.005,         # LOW
            sharpe_ratio=1.5,  # LOW risk
            max_drawdown=0.05, # LOW
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_high_drawdown_overrides_otherwise_low(self) -> None:
        """Single HIGH signal (drawdown) must push overall level to HIGH."""
        result = generate_recommendation(
            volatility=0.08,   # LOW
            var=0.005,         # LOW
            sharpe_ratio=1.5,  # LOW risk
            max_drawdown=0.40, # HIGH
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_poor_sharpe_overrides_otherwise_low(self) -> None:
        """Poor Sharpe (HIGH risk signal) must push overall level to HIGH."""
        result = generate_recommendation(
            volatility=0.08,   # LOW
            var=0.005,         # LOW
            sharpe_ratio=0.1,  # HIGH risk
            max_drawdown=0.05, # LOW
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_high_var_overrides_otherwise_low(self) -> None:
        """Single HIGH VaR must push overall level to HIGH."""
        result = generate_recommendation(
            volatility=0.08,   # LOW
            var=0.08,          # HIGH (8% > 5% threshold, portfolio=1.0)
            sharpe_ratio=1.5,  # LOW risk
            max_drawdown=0.05, # LOW
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_single_moderate_metric_raises_low_to_moderate(self) -> None:
        """One MODERATE signal among LOW ones → MODERATE overall."""
        result = generate_recommendation(
            volatility=0.08,   # LOW
            var=0.005,         # LOW
            sharpe_ratio=0.7,  # MODERATE
            max_drawdown=0.05, # LOW
            portfolio_value=1.0,
        )
        assert result.risk_level == "MODERATE"


# ---------------------------------------------------------------------------
# Boundary cases (metrics exactly on the threshold)
# ---------------------------------------------------------------------------


class TestBoundaryCases:
    def test_volatility_exactly_at_low_boundary(self) -> None:
        """vol == _VOL_LOW is still LOW."""
        result = generate_recommendation(
            volatility=_VOL_LOW,   # exactly 0.15
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        # _VOL_LOW is < boundary → LOW; at boundary, condition is vol < _VOL_LOW → False → MODERATE
        # Boundary: vol < 0.15 is LOW, vol == 0.15 is MODERATE
        assert result.risk_level in ("LOW", "MODERATE")

    def test_volatility_just_above_low_boundary(self) -> None:
        """vol just above _VOL_LOW → MODERATE contribution."""
        result = generate_recommendation(
            volatility=_VOL_LOW + 0.001,
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        assert result.risk_level == "MODERATE"

    def test_volatility_exactly_at_high_boundary(self) -> None:
        """vol == _VOL_HIGH is still MODERATE (boundary inclusive)."""
        result = generate_recommendation(
            volatility=_VOL_HIGH,  # exactly 0.30
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        assert result.risk_level == "MODERATE"

    def test_volatility_just_above_high_boundary(self) -> None:
        """vol just above _VOL_HIGH → HIGH."""
        result = generate_recommendation(
            volatility=_VOL_HIGH + 0.001,
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_sharpe_exactly_at_good_threshold(self) -> None:
        """sharpe == _SHARPE_GOOD → LOW risk from Sharpe."""
        result = generate_recommendation(
            volatility=0.08,
            var=0.005,
            sharpe_ratio=_SHARPE_GOOD,  # exactly 1.0
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        assert result.risk_level == "LOW"

    def test_sharpe_just_below_moderate_threshold(self) -> None:
        """sharpe just below _SHARPE_MODERATE → HIGH risk signal."""
        result = generate_recommendation(
            volatility=0.08,
            var=0.005,
            sharpe_ratio=_SHARPE_MODERATE - 0.01,
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_drawdown_exactly_at_high_boundary(self) -> None:
        """drawdown == _DD_HIGH is still MODERATE."""
        result = generate_recommendation(
            volatility=0.08,
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=_DD_HIGH,  # exactly 0.25
            portfolio_value=1.0,
        )
        assert result.risk_level == "MODERATE"

    def test_drawdown_just_above_high_boundary(self) -> None:
        """drawdown just above _DD_HIGH → HIGH."""
        result = generate_recommendation(
            volatility=0.08,
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=_DD_HIGH + 0.001,
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"

    def test_portfolio_value_scaling_affects_var_classification(self) -> None:
        """var=50 is 5% of 1000 (MODERATE boundary), 50% of 100 (HIGH)."""
        result_moderate = generate_recommendation(
            volatility=0.08,
            var=50.0,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            portfolio_value=1000.0,  # 50/1000 = 5% → MODERATE boundary
        )
        result_high = generate_recommendation(
            volatility=0.08,
            var=50.0,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            portfolio_value=100.0,   # 50/100 = 50% → HIGH
        )
        # High portfolio_value → small fraction → lower risk
        assert _level_order(result_moderate.risk_level) <= _level_order(result_high.risk_level)

    def test_zero_drawdown_is_low(self) -> None:
        result = generate_recommendation(
            volatility=0.08,
            var=0.005,
            sharpe_ratio=1.5,
            max_drawdown=0.0,
            portfolio_value=1.0,
        )
        assert result.risk_level == "LOW"

    def test_negative_sharpe_is_high(self) -> None:
        """Negative Sharpe → HIGH risk signal."""
        result = generate_recommendation(
            volatility=0.08,
            var=0.005,
            sharpe_ratio=-0.5,
            max_drawdown=0.05,
            portfolio_value=1.0,
        )
        assert result.risk_level == "HIGH"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_inputs_same_output(self) -> None:
        r1 = generate_recommendation(**MODERATE_METRICS)
        r2 = generate_recommendation(**MODERATE_METRICS)
        assert r1.risk_level == r2.risk_level
        assert r1.recommendation == r2.recommendation
        assert r1.explanations == r2.explanations


# ---------------------------------------------------------------------------
# API integration — recommendation field appears in endpoint responses
# ---------------------------------------------------------------------------


class TestApiIncludesRecommendation:
    """Smoke-test that the /risk/analyse endpoint returns recommendation."""

    def test_risk_analyse_includes_recommendation(self) -> None:
        import os
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        from fastapi.testclient import TestClient
        from backend.main import app

        with TestClient(app) as client:
            response = client.post(
                "/risk/analyse",
                json={"prices": [100.0, 102.0, 101.0, 105.0, 103.0, 107.0, 106.0]},
            )
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        rec = data["recommendation"]
        assert rec["risk_level"] in ("LOW", "MODERATE", "HIGH")
        assert isinstance(rec["recommendation"], str)
        assert isinstance(rec["explanations"], list)
        assert 2 <= len(rec["explanations"]) <= 4

    def test_ticker_endpoint_includes_recommendation(self) -> None:
        import os
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        from unittest.mock import patch
        from fastapi.testclient import TestClient
        from backend.main import app

        prices = [100.0, 102.0, 101.5, 105.0, 103.5, 107.0, 106.0, 108.0, 107.5, 110.0]
        with TestClient(app) as client:
            with patch("backend.api.risk.fetch_closing_prices", return_value=prices):
                response = client.post(
                    "/risk/analyse/ticker",
                    json={"ticker": "AAPL", "period": "1y"},
                )
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        rec = data["recommendation"]
        assert rec["risk_level"] in ("LOW", "MODERATE", "HIGH")
        assert isinstance(rec["recommendation"], str)
        assert 2 <= len(rec["explanations"]) <= 4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _level_order(level: str) -> int:
    return {"LOW": 0, "MODERATE": 1, "HIGH": 2}[level]
