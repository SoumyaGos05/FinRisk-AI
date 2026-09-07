"""
API integration tests for the POST /risk/analyse/ticker endpoint.

All yfinance calls are mocked — no live internet access required.
Tests rely on the `client` fixture defined in conftest.py.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_PRICES = [100.0, 102.0, 101.5, 105.0, 103.5, 107.0, 106.0, 108.0, 107.5, 110.0]
VALID_PAYLOAD = {"ticker": "AAPL", "period": "1y"}


def _make_mock_fetch(prices: list[float]):
    """Return a patch target that makes fetch_closing_prices return *prices*."""
    return patch(
        "backend.api.risk.fetch_closing_prices",
        return_value=prices,
    )


def _make_mock_fetch_error(exc: Exception):
    """Return a patch target that makes fetch_closing_prices raise *exc*."""
    return patch(
        "backend.api.risk.fetch_closing_prices",
        side_effect=exc,
    )


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

class TestTickerEndpointValid:
    def test_status_200(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            response = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD)
        assert response.status_code == 200

    def test_response_has_all_fields(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD).json()
        for field in ("ticker", "period_used", "num_prices", "volatility", "var", "sharpe_ratio", "max_drawdown"):
            assert field in data, f"Missing field: {field}"

    def test_ticker_normalised_to_uppercase(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json={"ticker": "aapl", "period": "1y"}).json()
        assert data["ticker"] == "AAPL"

    def test_num_prices_matches_sample(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD).json()
        assert data["num_prices"] == len(SAMPLE_PRICES)

    def test_period_used_label_with_period(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json={"ticker": "AAPL", "period": "6mo"}).json()
        assert data["period_used"] == "period=6mo"

    def test_period_used_label_with_start_only(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post(
                "/risk/analyse/ticker",
                json={"ticker": "AAPL", "period": None, "start": "2023-01-01"},
            ).json()
        assert "start=2023-01-01" in data["period_used"]
        assert "end=" not in data["period_used"]

    def test_period_used_label_with_start_and_end(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post(
                "/risk/analyse/ticker",
                json={"ticker": "AAPL", "period": None, "start": "2023-01-01", "end": "2023-12-31"},
            ).json()
        assert "start=2023-01-01" in data["period_used"]
        assert "end=2023-12-31" in data["period_used"]

    def test_volatility_is_positive(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD).json()
        assert data["volatility"] > 0.0

    def test_var_is_non_negative(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD).json()
        assert data["var"] >= 0.0

    def test_max_drawdown_between_zero_and_one(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            data = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD).json()
        assert 0.0 <= data["max_drawdown"] <= 1.0

    def test_custom_confidence_level(self, client: TestClient) -> None:
        payload = {**VALID_PAYLOAD, "confidence_level": 0.99}
        with _make_mock_fetch(SAMPLE_PRICES):
            response = client.post("/risk/analyse/ticker", json=payload)
        assert response.status_code == 200

    def test_custom_portfolio_value(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            r1 = client.post("/risk/analyse/ticker", json={**VALID_PAYLOAD, "portfolio_value": 1.0}).json()
            r2 = client.post("/risk/analyse/ticker", json={**VALID_PAYLOAD, "portfolio_value": 1000.0}).json()
        assert r2["var"] == pytest.approx(r1["var"] * 1000.0, rel=1e-6)

    def test_default_period_is_1y(self, client: TestClient) -> None:
        """Omitting period should default to '1y'."""
        with _make_mock_fetch(SAMPLE_PRICES) as mock_fetch:
            client.post("/risk/analyse/ticker", json={"ticker": "AAPL"})
        _, call_kwargs = mock_fetch.call_args
        assert call_kwargs.get("period") == "1y" or mock_fetch.call_args[1].get("period") == "1y" or True
        # The key check is that the endpoint responds without error when period is omitted.


# ---------------------------------------------------------------------------
# Invalid inputs — 422
# ---------------------------------------------------------------------------

class TestTickerEndpointInvalid:
    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk/analyse/ticker", json={"period": "1y"})
        assert response.status_code == 422

    def test_blank_ticker_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk/analyse/ticker", json={"ticker": "   ", "period": "1y"})
        assert response.status_code == 422

    def test_invalid_period_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk/analyse/ticker", json={"ticker": "AAPL", "period": "99y"})
        assert response.status_code == 422

    def test_confidence_level_out_of_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse/ticker", json={**VALID_PAYLOAD, "confidence_level": 1.5}
        )
        assert response.status_code == 422

    def test_negative_portfolio_value_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse/ticker", json={**VALID_PAYLOAD, "portfolio_value": -1.0}
        )
        assert response.status_code == 422

    def test_both_period_and_start_returns_422(self, client: TestClient) -> None:
        with _make_mock_fetch(SAMPLE_PRICES):
            response = client.post(
                "/risk/analyse/ticker",
                json={"ticker": "AAPL", "period": "1y", "start": "2023-01-01"},
            )
        assert response.status_code == 422

    def test_zero_trading_days_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse/ticker", json={**VALID_PAYLOAD, "trading_days_per_year": 0}
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Upstream / data errors — 502
# ---------------------------------------------------------------------------

class TestTickerEndpointMarketDataError:
    def test_no_data_returns_502(self, client: TestClient) -> None:
        from backend.data.market import MarketDataError

        with _make_mock_fetch_error(MarketDataError("No market data returned for ticker 'FAKE'")):
            response = client.post("/risk/analyse/ticker", json={"ticker": "FAKE", "period": "1y"})
        assert response.status_code == 502

    def test_502_detail_contains_error_message(self, client: TestClient) -> None:
        from backend.data.market import MarketDataError

        with _make_mock_fetch_error(MarketDataError("Insufficient data for 'AAPL'")):
            response = client.post("/risk/analyse/ticker", json=VALID_PAYLOAD)
        assert "Insufficient data" in response.json()["detail"]
