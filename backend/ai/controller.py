"""
AI Explanation Controller — gateway between the API layer and an AI provider.

Responsibilities:
  1. Fingerprint the deterministic metrics to key the cache.
  2. Return a cached explanation if one exists (zero provider calls).
  3. Enforce MAX_AI_CALLS_PER_ANALYSIS = 1.
  4. Call the configured AI provider exactly once on a cache miss.
  5. Store the result in a bounded LRU-style in-memory cache.
  6. Catch ALL provider errors and return a graceful fallback so the
     deterministic analysis is never blocked by an AI failure.

The cache is a module-level ordered dict bounded by _MAX_CACHE_SIZE.
It uses simple FIFO eviction (oldest entry dropped when full) which is
sufficient for this MVP workload.  No database or external service needed.

Security:
  - The API key is read from settings (the only allowed source).
  - The key never appears in logs, responses, or exceptions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import OrderedDict
from typing import Optional

from backend.ai.gemini import GeminiProvider
from backend.ai.provider import AIProviderError
from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bounded in-memory cache
# ---------------------------------------------------------------------------

_MAX_CACHE_SIZE: int = 128  # Maximum distinct analyses kept in memory
_cache: OrderedDict[str, str] = OrderedDict()  # fingerprint → explanation text

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_fingerprint(payload: dict) -> str:
    """
    Return a deterministic SHA-256 hex digest from the analysis payload.

    The digest is computed from a canonical JSON representation (sorted keys,
    fixed decimal precision) so that identical metric values always map to the
    same fingerprint regardless of floating-point noise at irrelevant precision.
    """
    canonical = json.dumps(
        {
            "risk": payload.get("risk", ""),
            "revenue_growth": round(float(payload.get("revenue_growth", 0.0)), 2),
            "profit_growth": round(float(payload.get("profit_growth", 0.0)), 2),
            "debt_to_equity": round(float(payload.get("debt_to_equity", 0.0)), 4),
            "current_ratio": round(float(payload.get("current_ratio", 0.0)), 4),
            "net_profit_margin": round(float(payload.get("net_profit_margin", 0.0)), 2),
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _cache_get(fingerprint: str) -> Optional[str]:
    """Return cached explanation or None; moves hit to MRU position."""
    if fingerprint in _cache:
        _cache.move_to_end(fingerprint)
        return _cache[fingerprint]
    return None


def _cache_set(fingerprint: str, text: str) -> None:
    """Store explanation; evict oldest entry if the cache is full."""
    if fingerprint in _cache:
        _cache.move_to_end(fingerprint)
    else:
        if len(_cache) >= _MAX_CACHE_SIZE:
            _cache.popitem(last=False)  # FIFO evict oldest
        _cache[fingerprint] = text


def _build_provider() -> Optional[GeminiProvider]:
    """
    Construct a GeminiProvider from settings.

    Returns None (silently) when the API key is absent or blank, which
    triggers the deterministic fallback path in get_ai_explanation().
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or not api_key.strip():
        return None
    try:
        return GeminiProvider(
            api_key=api_key,
            model=settings.GEMINI_MODEL,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
        )
    except AIProviderError:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_ai_explanation(payload: dict) -> Optional[str]:
    """
    Return a short AI-generated explanation for the supplied financial metrics,
    or None if the AI provider is unavailable or fails for any reason.

    The caller (API route) must always have deterministic results ready; this
    function's return value is an *optional* supplement — never a hard dependency.

    Args:
        payload: Compact dict produced by the API route after deterministic
                 calculation, e.g.::

                     {
                         "risk": "HIGH",
                         "revenue_growth": -7.4,
                         "profit_growth": -15.3,
                         "debt_to_equity": 2.5,
                         "current_ratio": 0.8,
                         "net_profit_margin": 5.0,
                     }

    Returns:
        Plain-text explanation string on success, or None on any failure.
    """
    fingerprint = _make_fingerprint(payload)

    # 1. Cache hit — zero provider calls
    cached = _cache_get(fingerprint)
    if cached is not None:
        logger.debug("AI explanation served from cache (fingerprint %s…)", fingerprint[:8])
        return cached

    # 2. No API key configured → silent fallback
    provider = _build_provider()
    if provider is None:
        logger.debug("AI explanation skipped: GEMINI_API_KEY not configured.")
        return None

    # 3. Single provider call (MAX_AI_CALLS_PER_ANALYSIS = 1)
    try:
        text = provider.explain(payload)
    except AIProviderError as exc:
        logger.warning("AI explanation unavailable: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001 — catch-all safety net
        logger.warning("Unexpected AI provider error: %s", type(exc).__name__)
        return None

    # 4. Store in bounded cache
    _cache_set(fingerprint, text)
    logger.debug("AI explanation cached (fingerprint %s…)", fingerprint[:8])
    return text


def cache_size() -> int:
    """Return the current number of entries in the explanation cache (for testing)."""
    return len(_cache)


def clear_cache() -> None:
    """Clear the explanation cache (for testing only)."""
    _cache.clear()
