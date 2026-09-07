"""
Tests for the pure-Python risk calculation engine.

Covers:
- Normal valid inputs
- Edge cases (constant prices, single-day drawdown, non-standard confidence level)
- Invalid inputs (too few prices, non-positive prices, bad confidence level, etc.)
"""

import math

import pytest

from backend.logic.risk_engine import (
    analyse_risk,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe,
    calculate_var,
    calculate_volatility,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

PRICES_5 = [100.0, 102.0, 101.0, 105.0, 103.0]
# Pre-computed returns for PRICES_5:
# 0.02, -0.00980392..., 0.03960396..., -0.01904762...
RETURNS_5 = [
    (PRICES_5[i] - PRICES_5[i - 1]) / PRICES_5[i - 1] for i in range(1, len(PRICES_5))
]

PRICES_FLAT = [50.0, 50.0, 50.0, 50.0]  # zero returns → zero std


# ---------------------------------------------------------------------------
# calculate_returns
# ---------------------------------------------------------------------------


class TestCalculateReturns:
    def test_basic_returns(self) -> None:
        """Returns should be (p_i - p_{i-1}) / p_{i-1}."""
        returns = calculate_returns([100.0, 110.0, 99.0])
        assert returns[0] == pytest.approx(0.10, rel=1e-6)
        assert returns[1] == pytest.approx(-0.10 / 1.10 * 1.1, rel=1e-6)

    def test_length_is_prices_minus_one(self) -> None:
        assert len(calculate_returns(PRICES_5)) == len(PRICES_5) - 1

    def test_two_prices_returns_one_return(self) -> None:
        result = calculate_returns([100.0, 105.0])
        assert result == pytest.approx([0.05], rel=1e-9)

    def test_fewer_than_two_prices_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            calculate_returns([100.0])

    def test_empty_prices_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            calculate_returns([])

    def test_zero_price_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_returns([100.0, 0.0, 105.0])

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_returns([100.0, -5.0])


# ---------------------------------------------------------------------------
# calculate_volatility
# ---------------------------------------------------------------------------


class TestCalculateVolatility:
    def test_positive_volatility(self) -> None:
        vol = calculate_volatility(RETURNS_5)
        assert vol > 0.0

    def test_annualisation_factor(self) -> None:
        """Changing trading_days_per_year should scale volatility by sqrt ratio."""
        vol_252 = calculate_volatility(RETURNS_5, trading_days_per_year=252)
        vol_365 = calculate_volatility(RETURNS_5, trading_days_per_year=365)
        assert vol_365 / vol_252 == pytest.approx(math.sqrt(365 / 252), rel=1e-6)

    def test_constant_returns_zero_volatility(self) -> None:
        """Flat prices → zero returns → zero standard deviation → zero vol."""
        returns = calculate_returns(PRICES_FLAT)
        assert calculate_volatility(returns) == pytest.approx(0.0, abs=1e-12)

    def test_fewer_than_two_returns_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            calculate_volatility([0.01])

    def test_non_positive_trading_days_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_volatility(RETURNS_5, trading_days_per_year=0)


# ---------------------------------------------------------------------------
# calculate_var
# ---------------------------------------------------------------------------


class TestCalculateVar:
    def test_var_is_non_negative(self) -> None:
        var = calculate_var(RETURNS_5)
        assert var >= 0.0

    def test_higher_confidence_gives_higher_var(self) -> None:
        var_95 = calculate_var(RETURNS_5, confidence_level=0.95)
        var_99 = calculate_var(RETURNS_5, confidence_level=0.99)
        assert var_99 >= var_95

    def test_portfolio_value_scales_var(self) -> None:
        var_1 = calculate_var(RETURNS_5, portfolio_value=1.0)
        var_1000 = calculate_var(RETURNS_5, portfolio_value=1000.0)
        assert var_1000 == pytest.approx(var_1 * 1000.0, rel=1e-6)

    def test_non_standard_confidence_level(self) -> None:
        """A confidence level not in the lookup table should still work."""
        var = calculate_var(RETURNS_5, confidence_level=0.97)
        assert var >= 0.0

    def test_fewer_than_two_returns_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            calculate_var([0.01])

    def test_invalid_confidence_level_raises(self) -> None:
        with pytest.raises(ValueError):
            calculate_var(RETURNS_5, confidence_level=1.0)

    def test_zero_confidence_level_raises(self) -> None:
        with pytest.raises(ValueError):
            calculate_var(RETURNS_5, confidence_level=0.0)

    def test_non_positive_portfolio_value_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_var(RETURNS_5, portfolio_value=0.0)

    def test_constant_returns_var_floored_at_zero(self) -> None:
        """Zero-volatility series: VaR should be 0 (floored)."""
        flat_returns = [0.0, 0.0, 0.0, 0.0]
        var = calculate_var(flat_returns)
        assert var == 0.0


# ---------------------------------------------------------------------------
# calculate_sharpe
# ---------------------------------------------------------------------------


class TestCalculateSharpe:
    def test_sharpe_type(self) -> None:
        result = calculate_sharpe(RETURNS_5)
        assert isinstance(result, float)

    def test_higher_risk_free_rate_lowers_sharpe(self) -> None:
        sharpe_0 = calculate_sharpe(RETURNS_5, risk_free_rate=0.0)
        sharpe_high = calculate_sharpe(RETURNS_5, risk_free_rate=0.10)
        assert sharpe_0 > sharpe_high

    def test_zero_volatility_returns_zero(self) -> None:
        """Flat returns → zero volatility → Sharpe is 0.0 (not a ZeroDivisionError)."""
        returns = calculate_returns(PRICES_FLAT)
        assert calculate_sharpe(returns) == 0.0

    def test_fewer_than_two_returns_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            calculate_sharpe([0.01])


# ---------------------------------------------------------------------------
# calculate_max_drawdown
# ---------------------------------------------------------------------------


class TestCalculateMaxDrawdown:
    def test_known_drawdown(self) -> None:
        """Peak=110, trough=88 → drawdown = (110-88)/110 ≈ 0.2."""
        prices = [100.0, 110.0, 88.0]
        dd = calculate_max_drawdown(prices)
        assert dd == pytest.approx(22 / 110, rel=1e-6)

    def test_monotonically_increasing_prices(self) -> None:
        """No decline → drawdown is 0."""
        assert calculate_max_drawdown([10.0, 20.0, 30.0, 40.0]) == pytest.approx(0.0)

    def test_drawdown_not_confused_by_later_recovery(self) -> None:
        """Recovery after a trough should not reduce the reported max drawdown."""
        prices = [100.0, 50.0, 200.0]  # 50% drawdown, then doubles
        assert calculate_max_drawdown(prices) == pytest.approx(0.50, rel=1e-6)

    def test_multiple_drawdowns_returns_maximum(self) -> None:
        prices = [100.0, 90.0, 95.0, 70.0, 80.0]
        # First drawdown: (100-90)/100 = 0.10
        # Second drawdown from peak 100: (100-70)/100 = 0.30
        assert calculate_max_drawdown(prices) == pytest.approx(0.30, rel=1e-6)

    def test_fewer_than_two_prices_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            calculate_max_drawdown([100.0])

    def test_non_positive_price_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_max_drawdown([100.0, 0.0, 90.0])


# ---------------------------------------------------------------------------
# analyse_risk (integration wrapper)
# ---------------------------------------------------------------------------


class TestAnalyseRisk:
    def test_returns_all_keys(self) -> None:
        result = analyse_risk(PRICES_5)
        assert set(result.keys()) == {"volatility", "var", "sharpe_ratio", "max_drawdown"}

    def test_values_are_floats(self) -> None:
        result = analyse_risk(PRICES_5)
        for v in result.values():
            assert isinstance(v, float)

    def test_consistent_with_individual_functions(self) -> None:
        """analyse_risk should produce identical results to calling each function."""
        result = analyse_risk(PRICES_5, confidence_level=0.99, portfolio_value=10_000.0)
        returns = [(PRICES_5[i] - PRICES_5[i - 1]) / PRICES_5[i - 1] for i in range(1, len(PRICES_5))]
        assert result["volatility"] == pytest.approx(
            calculate_volatility(returns), rel=1e-9
        )
        assert result["var"] == pytest.approx(
            calculate_var(returns, 0.99, 10_000.0), rel=1e-9
        )
        assert result["sharpe_ratio"] == pytest.approx(
            calculate_sharpe(returns), rel=1e-9
        )
        assert result["max_drawdown"] == pytest.approx(
            calculate_max_drawdown(PRICES_5), rel=1e-9
        )

    def test_too_few_prices_raises(self) -> None:
        with pytest.raises(ValueError):
            analyse_risk([100.0, 105.0])  # only 1 return → can't compute stdev
