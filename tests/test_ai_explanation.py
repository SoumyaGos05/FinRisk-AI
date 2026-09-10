"""
Tests for the AI Explanation Engine.

Covers:
  - Successful Gemini response
  - Gemini failure → deterministic fallback (ai_explanation.available=False)
  - Missing API key → not_configured fallback
  - Cache hit → no second Gemini provider call
  - Cache is bounded (max size respected)
  - Deterministic fields never modified by AI path
  - AI text is plain string, not HTML
  - /risk/financial endpoint contract (all required fields always present)
  - ai_explanation field present and typed correctly in API response
  - AI cannot modify overall_risk or metric values

All Gemini HTTP calls are mocked — tests run fully offline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.ai import controller as ai_controller
from backend.ai.gemini import GeminiProvider
from backend.ai.controller import (
    _make_fingerprint,
    cache_size,
    clear_cache,
    get_ai_explanation,
)
from backend.ai.provider import AIProviderError


# ---------------------------------------------------------------------------
# Shared demo payload (mirrors the financial risk demo data)
# ---------------------------------------------------------------------------

DEMO_FINANCIAL_PAYLOAD = {
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

AI_PAYLOAD = {
    "risk": "HIGH",
    "revenue_growth": -7.41,
    "profit_growth": -15.25,
    "debt_to_equity": 2.5,
    "current_ratio": 0.8,
    "net_profit_margin": 5.0,
}

FAKE_EXPLANATION = (
    "The company shows HIGH financial risk driven by declining revenue, "
    "falling profits, and very high leverage. Liquidity is also a concern. "
    "A qualified financial professional should review these results before "
    "any decisions are made."
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear the AI cache before and after every test for isolation."""
    clear_cache()
    yield
    clear_cache()


# ---------------------------------------------------------------------------
# Controller unit tests
# ---------------------------------------------------------------------------


class TestFingerprint:
    def test_same_values_produce_same_fingerprint(self) -> None:
        fp1 = _make_fingerprint(AI_PAYLOAD)
        fp2 = _make_fingerprint(AI_PAYLOAD)
        assert fp1 == fp2

    def test_different_risk_produces_different_fingerprint(self) -> None:
        p2 = {**AI_PAYLOAD, "risk": "LOW"}
        assert _make_fingerprint(AI_PAYLOAD) != _make_fingerprint(p2)

    def test_different_metric_produces_different_fingerprint(self) -> None:
        p2 = {**AI_PAYLOAD, "current_ratio": 1.5}
        assert _make_fingerprint(AI_PAYLOAD) != _make_fingerprint(p2)

    def test_fingerprint_is_64_hex_chars(self) -> None:
        fp = _make_fingerprint(AI_PAYLOAD)
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)


class TestGeminiProviderSecurity:
    def test_model_is_normalized_and_key_stays_out_of_url(self) -> None:
        """Model names are normalised and API key stays in the header, not in the URL."""
        provider = GeminiProvider("AIzaFakeKey123", "  models/gemini-2.5-flash  ", 10)
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "ok explanation"}]}}]
        }
        with patch("backend.ai.gemini.httpx.post", return_value=fake_response) as mock_post:
            text = provider.explain(AI_PAYLOAD)
        assert text == "ok explanation"
        assert provider._model == "gemini-2.5-flash"
        called_url = mock_post.call_args.args[0]
        assert "?key=" not in called_url
        assert mock_post.call_args.kwargs["headers"]["x-goog-api-key"] == "AIzaFakeKey123"

    def test_404_error_includes_safe_diagnostic_without_exposing_key(self) -> None:
        """HTTP 404s surface a safe decoded message but never log or return the API key."""
        provider = GeminiProvider("AIzaFakeKey123", "gemini-2.5-flash", 10)
        fake_response = MagicMock()
        fake_response.status_code = 404
        fake_response.text = '{"error":{"message":"models/gemini-2.5-flash is not found"}}'
        with patch("backend.ai.gemini.httpx.post", return_value=fake_response):
            with pytest.raises(Exception) as exc_info:
                provider.explain(AI_PAYLOAD)
        message = str(exc_info.value)
        assert "HTTP 404" in message
        assert "models/gemini-2.5-flash" in message
        assert "AIzaFakeKey123" not in message


class TestGetAIExplanation:
    def test_returns_none_when_api_key_missing(self) -> None:
        """No key configured → silent None, zero provider calls."""
        with patch.object(ai_controller, "_build_provider", return_value=None):
            result = get_ai_explanation(AI_PAYLOAD)
        assert result is None

    def test_returns_explanation_on_success(self) -> None:
        """Happy path: provider returns text → controller returns it."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            result = get_ai_explanation(AI_PAYLOAD)
        assert result == FAKE_EXPLANATION
        mock_provider.explain.assert_called_once()

    def test_returns_none_on_provider_error(self) -> None:
        """Provider raises AIProviderError → controller returns None, no crash."""
        mock_provider = MagicMock()
        mock_provider.explain.side_effect = AIProviderError("timeout")
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            result = get_ai_explanation(AI_PAYLOAD)
        assert result is None

    def test_returns_none_on_unexpected_exception(self) -> None:
        """Unexpected exception → controller returns None, no crash."""
        mock_provider = MagicMock()
        mock_provider.explain.side_effect = RuntimeError("boom")
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            result = get_ai_explanation(AI_PAYLOAD)
        assert result is None

    def test_cache_hit_returns_without_calling_provider(self) -> None:
        """Second identical call hits cache — provider is called exactly once."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            result1 = get_ai_explanation(AI_PAYLOAD)
            result2 = get_ai_explanation(AI_PAYLOAD)  # identical → cache hit
        assert result1 == FAKE_EXPLANATION
        assert result2 == FAKE_EXPLANATION
        # Provider.explain must have been called exactly once
        assert mock_provider.explain.call_count == 1

    def test_different_payload_calls_provider_again(self) -> None:
        """Different metrics fingerprint → separate provider call."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        payload2 = {**AI_PAYLOAD, "risk": "LOW", "debt_to_equity": 0.1}
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            get_ai_explanation(AI_PAYLOAD)
            get_ai_explanation(payload2)
        assert mock_provider.explain.call_count == 2

    def test_cache_size_increments_on_new_entries(self) -> None:
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            get_ai_explanation(AI_PAYLOAD)
        assert cache_size() == 1

    def test_cache_not_polluted_on_provider_failure(self) -> None:
        """A failed call must not write to the cache."""
        mock_provider = MagicMock()
        mock_provider.explain.side_effect = AIProviderError("error")
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            get_ai_explanation(AI_PAYLOAD)
        assert cache_size() == 0

    def test_cache_bounded_evicts_oldest(self) -> None:
        """Cache must not grow beyond _MAX_CACHE_SIZE."""
        from backend.ai.controller import _MAX_CACHE_SIZE

        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION

        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            for i in range(_MAX_CACHE_SIZE + 5):
                payload = {**AI_PAYLOAD, "current_ratio": float(i)}
                get_ai_explanation(payload)

        assert cache_size() <= _MAX_CACHE_SIZE


# ---------------------------------------------------------------------------
# API endpoint integration tests — /risk/financial with AI mocked
# ---------------------------------------------------------------------------


class TestFinancialRiskAPIWithAI:
    def test_endpoint_returns_200_with_successful_ai(self, client: TestClient) -> None:
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            response = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD)
        assert response.status_code == 200

    def test_ai_explanation_present_in_response(self, client: TestClient) -> None:
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            data = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD).json()
        assert "ai_explanation" in data
        ai = data["ai_explanation"]
        assert ai["available"] is True
        assert ai["text"] == FAKE_EXPLANATION

    def test_deterministic_fields_unchanged_when_ai_succeeds(
        self, client: TestClient
    ) -> None:
        """AI success must never change overall_risk or metric values."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            data = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD).json()
        # Deterministic engine produced HIGH for demo data — AI must not change it
        assert data["overall_risk"] == "HIGH"
        assert len(data["metrics"]) == 5
        # Metric values must be the deterministic values
        metric_map = {m["name"]: m for m in data["metrics"]}
        assert metric_map["Debt-to-Equity"]["value"] == pytest.approx(2.5, rel=1e-4)
        assert metric_map["Current Ratio"]["value"] == pytest.approx(0.8, rel=1e-4)

    def test_deterministic_fields_unchanged_when_ai_fails(
        self, client: TestClient
    ) -> None:
        """AI failure must not affect deterministic results or cause 500."""
        mock_provider = MagicMock()
        mock_provider.explain.side_effect = AIProviderError("network error")
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            response = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["overall_risk"] == "HIGH"
        assert len(data["metrics"]) == 5

    def test_ai_unavailable_field_on_provider_failure(
        self, client: TestClient
    ) -> None:
        mock_provider = MagicMock()
        mock_provider.explain.side_effect = AIProviderError("timeout")
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            data = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD).json()
        ai = data["ai_explanation"]
        assert ai["available"] is False
        assert ai["text"] is None

    def test_ai_not_configured_field_when_no_key(self, client: TestClient) -> None:
        """When no API key is configured, ai_explanation.error == 'not_configured'."""
        with patch.object(ai_controller, "_build_provider", return_value=None), \
             patch("backend.api.risk.app_settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            data = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD).json()
        ai = data["ai_explanation"]
        assert ai["available"] is False
        assert ai["error"] == "not_configured"

    def test_ai_explanation_text_is_plain_string(self, client: TestClient) -> None:
        """AI text must be a plain string — no HTML tags."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            data = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD).json()
        text = data["ai_explanation"]["text"]
        assert isinstance(text, str)
        assert "<" not in text  # no HTML tags in the mock text

    def test_one_ai_call_per_analysis(self, client: TestClient) -> None:
        """Submitting the same payload twice must not call the provider twice."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD)
            client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD)
        # Both requests share the same fingerprint → provider called exactly once
        assert mock_provider.explain.call_count == 1

    def test_existing_required_fields_still_present(self, client: TestClient) -> None:
        """Ensure all fields required by existing tests are still returned."""
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            data = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD).json()
        required = {
            "company_name", "overall_risk", "overall_explanation", "metrics",
            "current_revenue", "previous_revenue",
            "current_net_profit", "previous_net_profit",
        }
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_no_api_key_in_response_body(self, client: TestClient) -> None:
        """The Gemini API key must never appear in any response field."""
        fake_key = "AIzaSy_FAKE_KEY_FOR_TEST_12345"
        mock_provider = MagicMock()
        mock_provider.explain.return_value = FAKE_EXPLANATION
        with patch.object(ai_controller, "_build_provider", return_value=mock_provider):
            with patch("backend.ai.controller.settings") as mock_settings:
                mock_settings.GEMINI_API_KEY = fake_key
                mock_settings.GEMINI_MODEL = "gemini-3.6-flash"
                mock_settings.AI_TIMEOUT_SECONDS = 10
                response = client.post("/risk/financial", json=DEMO_FINANCIAL_PAYLOAD)
        assert fake_key not in response.text
