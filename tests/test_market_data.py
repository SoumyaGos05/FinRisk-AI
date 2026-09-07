"""
Tests for backend/data/market.py (market data ingestion).

All yfinance calls are mocked — no live internet access required.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from backend.data.market import MarketDataError, fetch_closing_prices


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_history(prices: list[float]) -> MagicMock:
    """Return a mock that looks like a yfinance DataFrame with a 'Close' column."""
    import pandas as pd

    df = pd.DataFrame({"Close": prices})
    return df


SAMPLE_PRICES = [100.0, 102.0, 101.5, 105.0, 103.5, 107.0, 106.0]


# ---------------------------------------------------------------------------
# fetch_closing_prices — valid inputs
# ---------------------------------------------------------------------------

class TestFetchClosingPricesValid:
    def test_returns_list_of_floats_with_period(self) -> None:
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_ticker_cls.return_value.history.return_value = _mock_history(SAMPLE_PRICES)
            result = fetch_closing_prices("AAPL", period="1y")
        assert result == SAMPLE_PRICES
        assert all(isinstance(p, float) for p in result)

    def test_ticker_is_uppercased_and_stripped(self) -> None:
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_ticker_cls.return_value.history.return_value = _mock_history(SAMPLE_PRICES)
            fetch_closing_prices("  aapl  ", period="1y")
        mock_ticker_cls.assert_called_once_with("AAPL")

    def test_passes_period_to_history(self) -> None:
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_inst = mock_ticker_cls.return_value
            mock_inst.history.return_value = _mock_history(SAMPLE_PRICES)
            fetch_closing_prices("MSFT", period="6mo")
        mock_inst.history.assert_called_once_with(period="6mo")

    def test_passes_start_to_history(self) -> None:
        start = date(2023, 1, 1)
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_inst = mock_ticker_cls.return_value
            mock_inst.history.return_value = _mock_history(SAMPLE_PRICES)
            fetch_closing_prices("GOOG", start=start)
        mock_inst.history.assert_called_once_with(start="2023-01-01")

    def test_passes_start_and_end_to_history(self) -> None:
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_inst = mock_ticker_cls.return_value
            mock_inst.history.return_value = _mock_history(SAMPLE_PRICES)
            fetch_closing_prices("GOOG", start=start, end=end)
        mock_inst.history.assert_called_once_with(start="2023-01-01", end="2023-12-31")

    def test_drops_nan_values(self) -> None:
        """NaN prices in yfinance output should be silently dropped."""
        import math
        import pandas as pd

        prices_with_nan = [100.0, float("nan"), 102.0, 103.0]
        df = pd.DataFrame({"Close": prices_with_nan})
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_ticker_cls.return_value.history.return_value = df
            result = fetch_closing_prices("AAPL", period="1mo")
        assert all(not math.isnan(p) for p in result)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# fetch_closing_prices — invalid / error cases
# ---------------------------------------------------------------------------

class TestFetchClosingPricesErrors:
    def test_empty_ticker_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            fetch_closing_prices("", period="1y")

    def test_whitespace_only_ticker_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            fetch_closing_prices("   ", period="1y")

    def test_both_period_and_start_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            fetch_closing_prices("AAPL", period="1y", start=date(2023, 1, 1))

    def test_neither_period_nor_start_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            fetch_closing_prices("AAPL")

    def test_empty_dataframe_raises_market_data_error(self) -> None:
        import pandas as pd

        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_ticker_cls.return_value.history.return_value = pd.DataFrame()
            with pytest.raises(MarketDataError, match="No market data"):
                fetch_closing_prices("UNKNOWN", period="1y")

    def test_too_few_prices_raises_market_data_error(self) -> None:
        """Only 2 prices — below the minimum of 3."""
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_ticker_cls.return_value.history.return_value = _mock_history([100.0, 102.0])
            with pytest.raises(MarketDataError, match="Insufficient data"):
                fetch_closing_prices("AAPL", period="1d")

    def test_none_history_raises_market_data_error(self) -> None:
        """yfinance returning None is handled gracefully."""
        with patch("backend.data.market.yf.Ticker") as mock_ticker_cls:
            mock_ticker_cls.return_value.history.return_value = None
            with pytest.raises(MarketDataError, match="No market data"):
                fetch_closing_prices("AAPL", period="1y")
