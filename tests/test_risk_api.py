"""
API integration tests for the /risk/analyse endpoint.

Uses FastAPI's TestClient — no live server required.
All tests rely on the `client` fixture defined in conftest.py.
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "prices": [100.0, 102.5, 101.0, 105.0, 103.0, 107.0, 106.0],
}


# ---------------------------------------------------------------------------
# /risk/analyse — happy paths
# ---------------------------------------------------------------------------


class TestRiskAnalyseValid:
    def test_status_200(self, client: TestClient) -> None:
        response = client.post("/risk/analyse", json=VALID_PAYLOAD)
        assert response.status_code == 200

    def test_response_has_required_fields(self, client: TestClient) -> None:
        data = client.post("/risk/analyse", json=VALID_PAYLOAD).json()
        assert "volatility" in data
        assert "var" in data
        assert "sharpe_ratio" in data
        assert "max_drawdown" in data

    def test_all_values_are_numbers(self, client: TestClient) -> None:
        data = client.post("/risk/analyse", json=VALID_PAYLOAD).json()
        for key in ("volatility", "var", "sharpe_ratio", "max_drawdown"):
            assert isinstance(data[key], (int, float)), f"{key} is not numeric"

    def test_volatility_is_positive_for_varying_prices(self, client: TestClient) -> None:
        data = client.post("/risk/analyse", json=VALID_PAYLOAD).json()
        assert data["volatility"] > 0.0

    def test_var_is_non_negative(self, client: TestClient) -> None:
        data = client.post("/risk/analyse", json=VALID_PAYLOAD).json()
        assert data["var"] >= 0.0

    def test_max_drawdown_between_zero_and_one(self, client: TestClient) -> None:
        data = client.post("/risk/analyse", json=VALID_PAYLOAD).json()
        assert 0.0 <= data["max_drawdown"] <= 1.0

    def test_custom_confidence_level(self, client: TestClient) -> None:
        payload = {**VALID_PAYLOAD, "confidence_level": 0.99}
        data = client.post("/risk/analyse", json=payload).json()
        assert data["var"] >= 0.0

    def test_custom_portfolio_value_scales_var(self, client: TestClient) -> None:
        r1 = client.post("/risk/analyse", json={**VALID_PAYLOAD, "portfolio_value": 1.0}).json()
        r2 = client.post("/risk/analyse", json={**VALID_PAYLOAD, "portfolio_value": 1000.0}).json()
        assert r2["var"] == pytest.approx(r1["var"] * 1000.0, rel=1e-6)

    def test_custom_risk_free_rate(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={**VALID_PAYLOAD, "risk_free_rate": 0.04}
        )
        assert response.status_code == 200

    def test_monotone_increasing_prices_zero_drawdown(self, client: TestClient) -> None:
        payload = {"prices": [10.0, 20.0, 30.0, 40.0, 50.0]}
        data = client.post("/risk/analyse", json=payload).json()
        assert data["max_drawdown"] == pytest.approx(0.0, abs=1e-12)

    def test_flat_prices_zero_volatility(self, client: TestClient) -> None:
        payload = {"prices": [50.0, 50.0, 50.0, 50.0, 50.0]}
        data = client.post("/risk/analyse", json=payload).json()
        assert data["volatility"] == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# /risk/analyse — invalid inputs (should return 422)
# ---------------------------------------------------------------------------


class TestRiskAnalyseInvalid:
    def test_fewer_than_three_prices_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk/analyse", json={"prices": [100.0, 105.0]})
        assert response.status_code == 422

    def test_empty_prices_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk/analyse", json={"prices": []})
        assert response.status_code == 422

    def test_missing_prices_field_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk/analyse", json={})
        assert response.status_code == 422

    def test_zero_price_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={"prices": [100.0, 0.0, 105.0, 103.0]}
        )
        assert response.status_code == 422

    def test_negative_price_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={"prices": [100.0, -5.0, 105.0, 103.0]}
        )
        assert response.status_code == 422

    def test_confidence_level_zero_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={**VALID_PAYLOAD, "confidence_level": 0.0}
        )
        assert response.status_code == 422

    def test_confidence_level_one_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={**VALID_PAYLOAD, "confidence_level": 1.0}
        )
        assert response.status_code == 422

    def test_negative_portfolio_value_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={**VALID_PAYLOAD, "portfolio_value": -100.0}
        )
        assert response.status_code == 422

    def test_zero_trading_days_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={**VALID_PAYLOAD, "trading_days_per_year": 0}
        )
        assert response.status_code == 422

    def test_non_numeric_prices_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/risk/analyse", json={"prices": ["a", "b", "c", "d"]}
        )
        assert response.status_code == 422
