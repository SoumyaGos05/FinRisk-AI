"""
Core financial risk calculation engine.

All functions are pure Python — no FastAPI, no database, no HTTP calls.
Each function is deterministic: given the same inputs it always returns the
same output, making it straightforward to unit-test.

Calculations implemented
------------------------
- ``calculate_returns``     : period-over-period simple returns from a price list
- ``calculate_volatility``  : annualised standard deviation of returns
- ``calculate_var``         : parametric (Gaussian) Value-at-Risk at a given confidence level
- ``calculate_sharpe``      : Sharpe ratio (excess return / volatility)
- ``calculate_max_drawdown``: maximum peak-to-trough percentage decline
- ``analyse_risk``          : convenience wrapper that computes all metrics at once
"""

import math
import statistics
from typing import Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# z-scores for common confidence levels — avoids a scipy/numpy dependency.
# Values are taken from standard normal distribution tables.
_Z_SCORES: dict[float, float] = {
    0.90: 1.281552,
    0.95: 1.644854,
    0.99: 2.326348,
}

# Default trading days per year used for annualisation.
_TRADING_DAYS_PER_YEAR: int = 252


def _z_score(confidence_level: float) -> float:
    """
    Return the one-tailed z-score for a given confidence level.

    The exact value is looked up from a pre-computed table for 0.90, 0.95,
    and 0.99. For other values the inverse-normal is approximated with the
    rational approximation from Abramowitz & Stegun §26.2.17 (max error
    ~4.5e-4), which is more than sufficient for MVP risk analysis.

    Args:
        confidence_level: A probability in (0, 1) exclusive, e.g. 0.95.

    Returns:
        The z-score corresponding to that confidence level.

    Raises:
        ValueError: If the confidence level is outside (0, 1).
    """
    if not (0.0 < confidence_level < 1.0):
        raise ValueError(
            f"confidence_level must be in (0, 1), got {confidence_level}"
        )
    if confidence_level in _Z_SCORES:
        return _Z_SCORES[confidence_level]
    # Rational approximation of the inverse normal CDF.
    p = confidence_level
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    z = t - (c0 + c1 * t + c2 * t**2) / (1.0 + d1 * t + d2 * t**2 + d3 * t**3)
    return z


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_returns(prices: list[float]) -> list[float]:
    """
    Compute period-over-period simple returns from a list of prices.

    Return_i = (price_i - price_{i-1}) / price_{i-1}

    Args:
        prices: An ordered list of positive asset prices (oldest first).
                Must contain at least two elements.

    Returns:
        A list of simple returns; length is ``len(prices) - 1``.

    Raises:
        ValueError: If ``prices`` has fewer than 2 elements or contains a
                    non-positive value.
    """
    if len(prices) < 2:
        raise ValueError("prices must contain at least 2 elements to compute returns")
    for i, p in enumerate(prices):
        if p <= 0:
            raise ValueError(f"All prices must be positive; got {p} at index {i}")
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]


def calculate_volatility(
    returns: list[float],
    trading_days_per_year: int = _TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute annualised volatility (standard deviation) of returns.

    Annualised vol = daily_std * sqrt(trading_days_per_year)

    Args:
        returns: A list of period returns (e.g. from ``calculate_returns``).
                 Must contain at least 2 values.
        trading_days_per_year: Number of trading days used for annualisation.
                               Defaults to 252 (equity market convention).

    Returns:
        Annualised volatility as a decimal (e.g. 0.20 means 20%).

    Raises:
        ValueError: If ``returns`` has fewer than 2 elements or
                    ``trading_days_per_year`` is not positive.
    """
    if len(returns) < 2:
        raise ValueError("returns must contain at least 2 elements to compute volatility")
    if trading_days_per_year <= 0:
        raise ValueError("trading_days_per_year must be a positive integer")
    daily_std = statistics.stdev(returns)
    return daily_std * math.sqrt(trading_days_per_year)


def calculate_var(
    returns: list[float],
    confidence_level: float = 0.95,
    portfolio_value: float = 1.0,
) -> float:
    """
    Compute parametric (Gaussian) Value-at-Risk.

    VaR = portfolio_value * (mean_return - z * std_return)

    A positive result means the portfolio could *lose* up to that amount
    at the given confidence level over one period.

    Args:
        returns: A list of period returns (at least 2 values).
        confidence_level: Probability in (0, 1) for the VaR threshold,
                          e.g. 0.95 means "loss not exceeded 95% of the time".
        portfolio_value: Total portfolio value in any currency unit.
                         Defaults to 1.0 (returns VaR as a fraction).

    Returns:
        VaR as a positive number representing the potential loss.

    Raises:
        ValueError: If inputs are invalid.
    """
    if len(returns) < 2:
        raise ValueError("returns must contain at least 2 elements to compute VaR")
    if portfolio_value <= 0:
        raise ValueError("portfolio_value must be positive")
    mean = statistics.mean(returns)
    std = statistics.stdev(returns)
    z = _z_score(confidence_level)
    var = portfolio_value * (z * std - mean)
    # VaR is reported as a positive loss figure; floor at zero so that a
    # strongly positive mean cannot produce a negative "loss".
    return max(var, 0.0)


def calculate_sharpe(
    returns: list[float],
    risk_free_rate: float = 0.0,
    trading_days_per_year: int = _TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute the annualised Sharpe ratio.

    Sharpe = (annualised_mean_return - risk_free_rate) / annualised_volatility

    Args:
        returns: A list of period returns (at least 2 values).
        risk_free_rate: Annualised risk-free rate as a decimal (e.g. 0.04 for 4%).
                        Defaults to 0.0.
        trading_days_per_year: Trading days per year for annualisation.

    Returns:
        Annualised Sharpe ratio (dimensionless).  Returns 0.0 if volatility
        is zero (i.e. a constant-return series).

    Raises:
        ValueError: If ``returns`` has fewer than 2 elements.
    """
    if len(returns) < 2:
        raise ValueError("returns must contain at least 2 elements to compute Sharpe ratio")
    annualised_mean = statistics.mean(returns) * trading_days_per_year
    vol = calculate_volatility(returns, trading_days_per_year)
    if vol == 0.0:
        return 0.0
    return (annualised_mean - risk_free_rate) / vol


def calculate_max_drawdown(prices: list[float]) -> float:
    """
    Compute the maximum peak-to-trough drawdown from a price series.

    Max drawdown = max((peak - trough) / peak) over all peak/trough pairs
    where trough comes after peak.

    Args:
        prices: An ordered list of positive asset prices (oldest first),
                at least 2 elements.

    Returns:
        Max drawdown as a positive decimal (e.g. 0.30 means 30% decline).
        Returns 0.0 if prices never decrease.

    Raises:
        ValueError: If ``prices`` has fewer than 2 elements or contains a
                    non-positive value.
    """
    if len(prices) < 2:
        raise ValueError("prices must contain at least 2 elements to compute max drawdown")
    for i, p in enumerate(prices):
        if p <= 0:
            raise ValueError(f"All prices must be positive; got {p} at index {i}")

    peak = prices[0]
    max_dd = 0.0
    for price in prices[1:]:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd


def analyse_risk(
    prices: list[float],
    confidence_level: float = 0.95,
    risk_free_rate: float = 0.0,
    portfolio_value: float = 1.0,
    trading_days_per_year: int = _TRADING_DAYS_PER_YEAR,
) -> dict[str, float]:
    """
    Compute all risk metrics from a price series in one call.

    Args:
        prices: Ordered list of positive asset prices (oldest first),
                at least 3 elements (need ≥2 returns for statistics).
        confidence_level: VaR confidence level in (0, 1).
        risk_free_rate: Annualised risk-free rate (decimal).
        portfolio_value: Portfolio value for VaR scaling.
        trading_days_per_year: Trading days per year.

    Returns:
        A dict with keys:
        - ``volatility``     : annualised volatility
        - ``var``            : parametric Value-at-Risk
        - ``sharpe_ratio``   : annualised Sharpe ratio
        - ``max_drawdown``   : maximum peak-to-trough drawdown

    Raises:
        ValueError: If any individual calculation raises.
    """
    returns = calculate_returns(prices)
    return {
        "volatility": calculate_volatility(returns, trading_days_per_year),
        "var": calculate_var(returns, confidence_level, portfolio_value),
        "sharpe_ratio": calculate_sharpe(returns, risk_free_rate, trading_days_per_year),
        "max_drawdown": calculate_max_drawdown(prices),
    }
