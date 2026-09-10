"""
AI provider abstract base.

Defines the minimal interface that every AI explanation provider must implement.
Swap providers by supplying a different concrete implementation to the controller —
the deterministic engine and API layer never change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Minimal interface for an AI explanation provider."""

    @abstractmethod
    def explain(self, payload: dict) -> str:
        """
        Generate a short plain-text explanation for the supplied financial metrics.

        Args:
            payload: Compact dict of already-calculated deterministic values, e.g.
                     {"risk": "HIGH", "revenue_growth": -7.4, ...}

        Returns:
            A short plain-text explanation string (≤ ~200 tokens).

        Raises:
            AIProviderError: On any provider-level failure (network, auth, parse).
        """


class AIProviderError(Exception):
    """Raised by any concrete AIProvider when a call cannot be completed."""
