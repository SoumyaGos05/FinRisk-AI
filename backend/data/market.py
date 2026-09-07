"""
Market data ingestion module.

Wraps yfinance to fetch historical closing prices for a given ticker.
This module is the **only** place in the codebase that imports yfinance,
keeping the external dependency isolated and easy to mock in tests.

Public surface
--------------
- ``fetch_closing_prices`` — fetch closing prices for a ticker + period/date range.
"""

from datetime import date
from typing import Optional

import yfinance as yf


class MarketDataError(Exception):
    """Raised when market data cannot be fetched or is unusable."""


def fetch_closing_prices(
    ticker: str,
    period: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> list[float]:
    """
    Fetch historical adjusted closing prices for *ticker*.

    Exactly one of ``period`` or ``start`` (with optional ``end``) must be
    provided.  When ``start`` is given without ``end``, today's date is used
    as the upper bound.

    Parameters
    ----------
    ticker:
        Stock ticker symbol, e.g. ``"AAPL"`` or ``"MSFT"``.
    period:
        A yfinance period string such as ``"1mo"``, ``"3mo"``, ``"6mo"``,
        ``"1y"``, ``"2y"``, ``"5y"``, ``"ytd"``, or ``"max"``.
        Mutually exclusive with ``start``/``end``.
    start:
        Start date for the historical range (inclusive).
    end:
        End date for the historical range (exclusive).  Defaults to today
        when ``start`` is provided but ``end`` is omitted.

    Returns
    -------
    list[float]
        Adjusted closing prices ordered oldest-first.  Always contains at
        least 3 elements (the minimum required by the risk engine).

    Raises
    ------
    ValueError
        If neither or both of ``period`` and ``start`` are supplied, or if
        ``ticker`` is empty.
    MarketDataError
        If yfinance returns no data, or fewer than 3 data points.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    if (period is None) == (start is None):
        raise ValueError(
            "Provide exactly one of 'period' or 'start' (with optional 'end')"
        )

    t = yf.Ticker(ticker)

    if period is not None:
        hist = t.history(period=period)
    else:
        kwargs: dict = {"start": start.isoformat()}
        if end is not None:
            kwargs["end"] = end.isoformat()
        hist = t.history(**kwargs)

    if hist is None or len(hist) == 0:
        raise MarketDataError(
            f"No market data returned for ticker '{ticker}'. "
            "Check the symbol and date range."
        )

    # yfinance returns a DataFrame with a 'Close' column (or 'Adj Close'
    # depending on the version/auto_adjust setting).  We prefer 'Close'
    # because yfinance ≥ 0.2 applies split/dividend adjustment by default.
    close_col = "Close" if "Close" in hist.columns else "Adj Close"
    if close_col not in hist.columns:
        raise MarketDataError(
            f"Expected a 'Close' column in yfinance response for '{ticker}'; "
            f"got columns: {list(hist.columns)}"
        )

    prices = [float(p) for p in hist[close_col].dropna().tolist()]

    if len(prices) < 3:
        raise MarketDataError(
            f"Insufficient data for '{ticker}': need at least 3 closing prices, "
            f"got {len(prices)}. Try a longer date range or period."
        )

    return prices
