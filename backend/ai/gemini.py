"""
Google Gemini AI provider — direct REST implementation via httpx.

Uses the Gemini Developer API v1beta generateContent endpoint.
No Google SDK is required; httpx (already a project dependency) handles HTTP.

Authentication: API key passed as a query parameter (?key=...).
This credential must NEVER appear in logs, responses, or frontend code.
Only backend/config.py supplies the key — never read os.environ here.

Responsible AI constraints enforced by system_instruction:
  - Do not recalculate or invent values
  - Do not override the deterministic risk classification
  - Do not provide professional financial advice
  - Recommend human/professional review
"""

from __future__ import annotations

import json
import logging

import httpx

from backend.ai.provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System instruction sent with every request (counts toward input tokens).
# Kept compact to minimise cost/latency.
# ---------------------------------------------------------------------------
_SYSTEM_INSTRUCTION = (
    "You are an explanation assistant for FinRisk AI. "
    "You receive financial metrics already calculated by a deterministic engine. "
    "Do not recalculate, modify, or invent any numerical value. "
    "Explain only the supplied results in plain language. "
    "Do not change or override the supplied risk classification. "
    "Do not provide investment, lending, credit, trading, tax, "
    "or professional financial advice. "
    "Recommend that consequential decisions receive professional human review. "
    "Reply in 2-4 concise sentences only."
)

# ---------------------------------------------------------------------------
# User prompt template — filled with compact deterministic values only.
# The company name is intentionally excluded (not needed for explanation).
# ---------------------------------------------------------------------------
_USER_PROMPT_TEMPLATE = (
    "The deterministic financial analysis produced these results:\n"
    "Overall risk: {risk}\n"
    "Revenue Growth: {revenue_growth:.1f}%\n"
    "Profit Growth: {profit_growth:.1f}%\n"
    "Debt-to-Equity: {debt_to_equity:.2f}x\n"
    "Current Ratio: {current_ratio:.2f}x\n"
    "Net Profit Margin: {net_profit_margin:.1f}%\n\n"
    "In 2-4 concise sentences, explain what these results indicate "
    "about the company's financial health and what a reviewer should pay attention to."
)

_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AIProvider):
    """
    Calls the Google Gemini generateContent REST API via httpx.

    Args:
        api_key:         Google AI Studio API key.
        model:           Gemini model ID, e.g. 'gemini-2.5-flash'.
        timeout_seconds: HTTP timeout for the provider call.
    """

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 10) -> None:
        if not api_key or not api_key.strip():
            raise AIProviderError("GEMINI_API_KEY is missing or empty.")
        self._api_key = api_key.strip()
        self._model = model.strip()
        self._timeout = timeout_seconds

    def explain(self, payload: dict) -> str:
        """
        Call Gemini generateContent and return the explanation as plain text.

        Raises:
            AIProviderError: On network errors, HTTP errors, timeouts, or
                             malformed/empty responses.
        """
        prompt = _USER_PROMPT_TEMPLATE.format(
            risk=payload.get("risk", "UNKNOWN"),
            revenue_growth=float(payload.get("revenue_growth", 0.0)),
            profit_growth=float(payload.get("profit_growth", 0.0)),
            debt_to_equity=float(payload.get("debt_to_equity", 0.0)),
            current_ratio=float(payload.get("current_ratio", 0.0)),
            net_profit_margin=float(payload.get("net_profit_margin", 0.0)),
        )

        request_body = {
            "system_instruction": {
                "parts": [{"text": _SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "maxOutputTokens": 200,
                "temperature": 0.2,
            },
        }

        url = f"{_GEMINI_API_BASE}/{self._model}:generateContent?key={self._api_key}"

        try:
            response = httpx.post(
                url,
                json=request_body,
                headers={"x-goog-api-key": self._api_key},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise AIProviderError("Gemini request timed out.") from exc
        except httpx.RequestError as exc:
            raise AIProviderError(f"Gemini network error: {exc}") from exc

        if response.status_code != 200:
            # Log status (never log the key — it's in the URL query param,
            # but httpx does not expose it in the exception message).
            logger.warning(
                "Gemini API returned HTTP %s", response.status_code
            )
            raise AIProviderError(
                f"Gemini API error: HTTP {response.status_code}"
            )

        try:
            data = response.json()
        except Exception as exc:
            raise AIProviderError("Gemini response is not valid JSON.") from exc

        # Extract text from candidates[0].content.parts[0].text
        try:
            text: str = (
                data["candidates"][0]["content"]["parts"][0]["text"]
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                "Gemini response missing expected text field."
            ) from exc

        text = text.strip()
        if not text:
            raise AIProviderError("Gemini returned an empty explanation.")

        return text
