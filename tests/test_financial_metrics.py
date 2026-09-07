"""
Tests for the Prototype Financial Risk Indicator calculation engine.

Covers:
- All five metric calculations (happy path)
- Edge cases: zero denominators, negative values, boundary thresholds
- Risk classification for each metric
- Overall risk classification (worst-signal logic)
- Demo data (Demo Manufacturing Ltd.) produces expected values
- Invalid inputs raise ValueError
- API endpoint integration via TestClient
"""

import pytest
from fastapi.testclient import TestClient

from backend.logic.financial_metrics import (
    analyse_financial_risk,
    calculate_current_ratio,
    calculate_debt_to_equity,
    calculate_net_profit_margin,
    calculate_profit_growth,
    calculate_revenue_growth,
)


# ---------------------------------------------------------------------------
# Demo data constants (as specified in the product requirements)
# ---------------------------------------------------------------------------

DEMO = {
    "company_name": "Demo Manufacturing Ltd.",
    "current_revenue": 10_000_000.0,
    "previous_revenue": 10_800_000.0,
    "current_net_profit": 500_000.0,
    "previous_net_profit": 590_000.0,
    "total_debt": 2_500_000.0,
    "shareholders_equity": 1_000_000.0,
    "current_assets": 1_200_000.0,
    "current_liabilities": 1_500_000.0,
}


# ---------------------------------------------------------------------------
# calculate_revenue_growth
# ---------------------------------------------------------------------------


class TestCalculateRevenueGrowth:
    def test_positive_growth(self) -> None:
        result = calculate_revenue_growth(110.0, 100.0)
        assert result == pytest.approx(10.0, rel=1e-6)

    def test_negative_growth(self) -> None:
        result = calculate_revenue_growth(90.0, 100.0)
        assert result == pytest.approx(-10.0, rel=1e-6)

    def test_no_growth(self) -> None:
        result = calculate_revenue_growth(100.0, 100.0)
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_zero_previous_raises(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            calculate_revenue_growth(100.0, 0.0)

    def test_demo_revenue_growth(self) -> None:
        """Demo data: (10M - 10.8M) / 10.8M * 100 ≈ -7.41%"""
        result = calculate_revenue_growth(10_000_000.0, 10_800_000.0)
        expected = (10_000_000.0 - 10_800_000.0) / 10_800_000.0 * 100.0
        assert result == pytest.approx(expected, rel=1e-6)
        assert result < 0.0  # revenue declined


# ---------------------------------------------------------------------------
# calculate_profit_growth
# ---------------------------------------------------------------------------


class TestCalculateProfitGrowth:
    def test_positive_growth(self) -> None:
        result = calculate_profit_growth(120.0, 100.0)
        assert result == pytest.approx(20.0, rel=1e-6)

    def test_negative_growth(self) -> None:
        result = calculate_profit_growth(80.0, 100.0)
        assert result == pytest.approx(-20.0, rel=1e-6)

    def test_zero_previous_raises(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            calculate_profit_growth(100.0, 0.0)

    def test_negative_profit_current(self) -> None:
        """Current loss is valid input."""
        result = calculate_profit_growth(-50.0, 100.0)
        assert result == pytest.approx(-150.0, rel=1e-6)

    def test_demo_profit_growth(self) -> None:
        """Demo data: (500k - 590k) / 590k * 100 ≈ -15.25%"""
        result = calculate_profit_growth(500_000.0, 590_000.0)
        expected = (500_000.0 - 590_000.0) / 590_000.0 * 100.0
        assert result == pytest.approx(expected, rel=1e-6)
        assert result < -10.0  # exceeds high concern threshold


# ---------------------------------------------------------------------------
# calculate_debt_to_equity
# ---------------------------------------------------------------------------


class TestCalculateDebtToEquity:
    def test_basic_calculation(self) -> None:
        result = calculate_debt_to_equity(500.0, 1000.0)
        assert result == pytest.approx(0.5, rel=1e-6)

    def test_zero_equity_raises(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            calculate_debt_to_equity(100.0, 0.0)

    def test_no_debt(self) -> None:
        result = calculate_debt_to_equity(0.0, 1000.0)
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_very_high_dte(self) -> None:
        result = calculate_debt_to_equity(3000.0, 1000.0)
        assert result == pytest.approx(3.0, rel=1e-6)

    def test_demo_dte(self) -> None:
        """Demo data: 2.5M / 1M = 2.5x"""
        result = calculate_debt_to_equity(2_500_000.0, 1_000_000.0)
        assert result == pytest.approx(2.5, rel=1e-6)


# ---------------------------------------------------------------------------
# calculate_current_ratio
# ---------------------------------------------------------------------------


class TestCalculateCurrentRatio:
    def test_basic_calculation(self) -> None:
        result = calculate_current_ratio(200.0, 100.0)
        assert result == pytest.approx(2.0, rel=1e-6)

    def test_below_one(self) -> None:
        result = calculate_current_ratio(80.0, 100.0)
        assert result == pytest.approx(0.8, rel=1e-6)

    def test_zero_liabilities_raises(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            calculate_current_ratio(100.0, 0.0)

    def test_demo_current_ratio(self) -> None:
        """Demo data: 1.2M / 1.5M = 0.8x (liquidity concern)"""
        result = calculate_current_ratio(1_200_000.0, 1_500_000.0)
        assert result == pytest.approx(0.8, rel=1e-6)
        assert result < 1.0  # below liquidity concern threshold


# ---------------------------------------------------------------------------
# calculate_net_profit_margin
# ---------------------------------------------------------------------------


class TestCalculateNetProfitMargin:
    def test_basic_calculation(self) -> None:
        result = calculate_net_profit_margin(20.0, 100.0)
        assert result == pytest.approx(20.0, rel=1e-6)

    def test_negative_margin(self) -> None:
        result = calculate_net_profit_margin(-10.0, 100.0)
        assert result == pytest.approx(-10.0, rel=1e-6)

    def test_zero_revenue_raises(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            calculate_net_profit_margin(10.0, 0.0)

    def test_demo_npm(self) -> None:
        """Demo data: 500k / 10M * 100 = 5.0%"""
        result = calculate_net_profit_margin(500_000.0, 10_000_000.0)
        assert result == pytest.approx(5.0, rel=1e-6)


# ---------------------------------------------------------------------------
# analyse_financial_risk — overall integration
# ---------------------------------------------------------------------------


class TestAnalyseFinancialRisk:
    def test_returns_result_with_five_metrics(self) -> None:
        result = analyse_financial_risk(**DEMO)
        assert len(result.metrics) == 5

    def test_metric_names(self) -> None:
        result = analyse_financial_risk(**DEMO)
        names = [m.name for m in result.metrics]
        assert "Revenue Growth" in names
        assert "Profit Growth" in names
        assert "Debt-to-Equity" in names
        assert "Current Ratio" in names
        assert "Net Profit Margin" in names

    def test_overall_risk_is_valid_level(self) -> None:
        result = analyse_financial_risk(**DEMO)
        assert result.overall_risk in ("LOW", "MODERATE", "HIGH")

    def test_demo_data_overall_risk_is_high(self) -> None:
        """
        Demo data has DTE=2.5 (very high) and CR=0.8 (liquidity concern)
        so overall must be HIGH.
        """
        result = analyse_financial_risk(**DEMO)
        assert result.overall_risk == "HIGH"

    def test_company_name_preserved(self) -> None:
        result = analyse_financial_risk(**DEMO)
        assert result.company_name == "Demo Manufacturing Ltd."

    def test_low_risk_scenario(self) -> None:
        """A healthy company should score LOW overall."""
        result = analyse_financial_risk(
            company_name="Healthy Co.",
            current_revenue=12_000_000.0,
            previous_revenue=10_000_000.0,  # +20% growth → LOW
            current_net_profit=2_000_000.0,
            previous_net_profit=1_500_000.0,  # +33% → LOW
            total_debt=200_000.0,
            shareholders_equity=2_000_000.0,  # DTE=0.1 → LOW
            current_assets=5_000_000.0,
            current_liabilities=2_000_000.0,  # CR=2.5 → LOW
        )
        assert result.overall_risk == "LOW"

    def test_worst_signal_drives_overall(self) -> None:
        """Even one HIGH metric should push overall to HIGH."""
        result = analyse_financial_risk(
            company_name="Mixed Co.",
            current_revenue=11_000_000.0,
            previous_revenue=10_000_000.0,  # +10% → LOW
            current_net_profit=1_500_000.0,
            previous_net_profit=1_000_000.0,  # +50% → LOW
            total_debt=5_000_000.0,
            shareholders_equity=1_000_000.0,  # DTE=5.0 → HIGH
            current_assets=3_000_000.0,
            current_liabilities=1_000_000.0,  # CR=3.0 → LOW
        )
        assert result.overall_risk == "HIGH"

    def test_zero_previous_revenue_raises(self) -> None:
        bad = {**DEMO, "previous_revenue": 0.0}
        with pytest.raises(ValueError):
            analyse_financial_risk(**bad)

    def test_zero_previous_profit_raises(self) -> None:
        bad = {**DEMO, "previous_net_profit": 0.0}
        with pytest.raises(ValueError):
            analyse_financial_risk(**bad)

    def test_zero_equity_raises(self) -> None:
        bad = {**DEMO, "shareholders_equity": 0.0}
        with pytest.raises(ValueError):
            analyse_financial_risk(**bad)

    def test_zero_liabilities_raises(self) -> None:
        bad = {**DEMO, "current_liabilities": 0.0}
        with pytest.raises(ValueError):
            analyse_financial_risk(**bad)

    def test_zero_revenue_raises(self) -> None:
        bad = {**DEMO, "current_revenue": 0.0}
        with pytest.raises(ValueError):
            analyse_financial_risk(**bad)

    def test_metric_levels_are_valid(self) -> None:
        result = analyse_financial_risk(**DEMO)
        for m in result.metrics:
            assert m.level in ("LOW", "MODERATE", "HIGH")

    def test_metric_formatted_value_not_empty(self) -> None:
        result = analyse_financial_risk(**DEMO)
        for m in result.metrics:
            assert m.formatted_value.strip() != ""

    def test_threshold_notes_present(self) -> None:
        result = analyse_financial_risk(**DEMO)
        for m in result.metrics:
            assert "Prototype" in m.threshold_note


# ---------------------------------------------------------------------------
# Risk classification boundary tests
# ---------------------------------------------------------------------------


class TestRiskClassificationBoundaries:
    """Boundary-value tests for each metric's prototype thresholds."""

    def _base_result(self, **overrides):
        kwargs = {**DEMO, **overrides}
        return analyse_financial_risk(**kwargs)

    # Revenue growth boundaries
    def test_rev_growth_exactly_10_is_low(self) -> None:
        # current = previous * 1.10 → exactly +10%
        r = analyse_financial_risk(
            **{**DEMO, "current_revenue": DEMO["previous_revenue"] * 1.10}
        )
        rg = next(m for m in r.metrics if m.name == "Revenue Growth")
        assert rg.level == "LOW"

    def test_rev_growth_zero_is_moderate(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_revenue": DEMO["previous_revenue"]}
        )
        rg = next(m for m in r.metrics if m.name == "Revenue Growth")
        assert rg.level == "MODERATE"

    def test_rev_growth_negative_is_high(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_revenue": DEMO["previous_revenue"] * 0.9}
        )
        rg = next(m for m in r.metrics if m.name == "Revenue Growth")
        assert rg.level == "HIGH"

    # Profit growth boundaries
    def test_profit_growth_positive_is_low(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_net_profit": DEMO["previous_net_profit"] * 1.01}
        )
        pg = next(m for m in r.metrics if m.name == "Profit Growth")
        assert pg.level == "LOW"

    def test_profit_growth_neg_10_is_moderate(self) -> None:
        # exactly -10%
        r = analyse_financial_risk(
            **{**DEMO, "current_net_profit": DEMO["previous_net_profit"] * 0.90}
        )
        pg = next(m for m in r.metrics if m.name == "Profit Growth")
        assert pg.level == "MODERATE"

    def test_profit_growth_below_neg_10_is_high(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_net_profit": DEMO["previous_net_profit"] * 0.85}
        )
        pg = next(m for m in r.metrics if m.name == "Profit Growth")
        assert pg.level == "HIGH"

    # Debt-to-equity boundaries
    def test_dte_below_0_5_is_low(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "total_debt": DEMO["shareholders_equity"] * 0.4}
        )
        dte = next(m for m in r.metrics if m.name == "Debt-to-Equity")
        assert dte.level == "LOW"

    def test_dte_exactly_0_5_is_moderate(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "total_debt": DEMO["shareholders_equity"] * 0.5}
        )
        dte = next(m for m in r.metrics if m.name == "Debt-to-Equity")
        assert dte.level == "MODERATE"

    def test_dte_above_2_is_high(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "total_debt": DEMO["shareholders_equity"] * 2.5}
        )
        dte = next(m for m in r.metrics if m.name == "Debt-to-Equity")
        assert dte.level == "HIGH"

    # Current ratio boundaries
    def test_cr_above_2_is_low(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_assets": DEMO["current_liabilities"] * 2.5}
        )
        cr = next(m for m in r.metrics if m.name == "Current Ratio")
        assert cr.level == "LOW"

    def test_cr_between_1_and_2_is_moderate(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_assets": DEMO["current_liabilities"] * 1.5}
        )
        cr = next(m for m in r.metrics if m.name == "Current Ratio")
        assert cr.level == "MODERATE"

    def test_cr_below_1_is_high(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_assets": DEMO["current_liabilities"] * 0.8}
        )
        cr = next(m for m in r.metrics if m.name == "Current Ratio")
        assert cr.level == "HIGH"

    # Net profit margin boundaries
    def test_npm_above_10_is_low(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_net_profit": DEMO["current_revenue"] * 0.15}
        )
        npm = next(m for m in r.metrics if m.name == "Net Profit Margin")
        assert npm.level == "LOW"

    def test_npm_5_to_10_is_moderate(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_net_profit": DEMO["current_revenue"] * 0.07}
        )
        npm = next(m for m in r.metrics if m.name == "Net Profit Margin")
        assert npm.level == "MODERATE"

    def test_npm_negative_is_high(self) -> None:
        r = analyse_financial_risk(
            **{**DEMO, "current_net_profit": -DEMO["current_revenue"] * 0.05}
        )
        npm = next(m for m in r.metrics if m.name == "Net Profit Margin")
        assert npm.level == "HIGH"


# ---------------------------------------------------------------------------
# API integration tests — /risk/financial endpoint
# ---------------------------------------------------------------------------


DEMO_PAYLOAD = {
    "company_name": "Demo Manufacturing Ltd.",
    "current_revenue": 10_000_000.0,
    "previous_revenue": 10_800_000.0,
    "current_net_profit": 500_000.0,
    "previous_net_profit": 590_000.0,
    "total_debt": 2_500_000.0,
    "shareholders_equity": 1_000_000.0,
    "current_assets": 1_200_000.0,
    "current_liabilities": 1_500_000.0,
}


class TestFinancialRiskAPI:
    def test_status_200(self, client: TestClient) -> None:
        response = client.post("/risk/financial", json=DEMO_PAYLOAD)
        assert response.status_code == 200

    def test_response_fields_present(self, client: TestClient) -> None:
        data = client.post("/risk/financial", json=DEMO_PAYLOAD).json()
        assert "company_name" in data
        assert "overall_risk" in data
        assert "metrics" in data
        assert "overall_explanation" in data

    def test_demo_data_returns_high(self, client: TestClient) -> None:
        data = client.post("/risk/financial", json=DEMO_PAYLOAD).json()
        assert data["overall_risk"] == "HIGH"

    def test_five_metrics_returned(self, client: TestClient) -> None:
        data = client.post("/risk/financial", json=DEMO_PAYLOAD).json()
        assert len(data["metrics"]) == 5

    def test_overall_risk_is_valid(self, client: TestClient) -> None:
        data = client.post("/risk/financial", json=DEMO_PAYLOAD).json()
        assert data["overall_risk"] in ("LOW", "MODERATE", "HIGH")

    def test_missing_field_returns_422(self, client: TestClient) -> None:
        bad = {k: v for k, v in DEMO_PAYLOAD.items() if k != "current_revenue"}
        response = client.post("/risk/financial", json=bad)
        assert response.status_code == 422

    def test_zero_previous_revenue_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/financial", json={**DEMO_PAYLOAD, "previous_revenue": 0.0}
        )
        assert response.status_code == 422

    def test_zero_previous_profit_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/financial", json={**DEMO_PAYLOAD, "previous_net_profit": 0.0}
        )
        assert response.status_code == 422

    def test_zero_equity_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/financial", json={**DEMO_PAYLOAD, "shareholders_equity": 0.0}
        )
        assert response.status_code == 422

    def test_zero_current_revenue_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/financial", json={**DEMO_PAYLOAD, "current_revenue": 0.0}
        )
        assert response.status_code == 422

    def test_negative_debt_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/financial", json={**DEMO_PAYLOAD, "total_debt": -100.0}
        )
        assert response.status_code == 422

    def test_company_name_in_response(self, client: TestClient) -> None:
        data = client.post("/risk/financial", json=DEMO_PAYLOAD).json()
        assert data["company_name"] == "Demo Manufacturing Ltd."

    def test_trend_fields_present(self, client: TestClient) -> None:
        data = client.post("/risk/financial", json=DEMO_PAYLOAD).json()
        assert "current_revenue" in data
        assert "previous_revenue" in data
        assert "current_net_profit" in data
        assert "previous_net_profit" in data
