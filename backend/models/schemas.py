"""
Pydantic request/response schemas.

Keep ORM models (orm.py) and Pydantic schemas (this file) separate.
Add new schemas here as domain features are introduced.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.logic.recommender import RiskRecommendation


class HealthResponse(BaseModel):
    """Response schema for the /health endpoint."""

    status: str


# ---------------------------------------------------------------------------
# Risk Analysis schemas
# ---------------------------------------------------------------------------


class RiskAnalysisRequest(BaseModel):
    """Request body for the /risk/analyse endpoint."""

    prices: list[float] = Field(
        ...,
        min_length=3,
        description=(
            "Ordered list of positive asset prices (oldest first). "
            "Must contain at least 3 values so that at least 2 returns "
            "can be computed and statistics are meaningful."
        ),
        examples=[[100.0, 102.5, 101.0, 105.0, 103.0]],
    )
    confidence_level: float = Field(
        default=0.95,
        gt=0.0,
        lt=1.0,
        description="VaR confidence level in (0, 1). Defaults to 0.95.",
    )
    risk_free_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Annualised risk-free rate as a decimal, e.g. 0.04 for 4%.",
    )
    portfolio_value: float = Field(
        default=1.0,
        gt=0.0,
        description="Total portfolio value used to scale VaR output.",
    )
    trading_days_per_year: int = Field(
        default=252,
        gt=0,
        description="Trading days per year used for annualisation.",
    )

    @field_validator("prices")
    @classmethod
    def prices_must_be_positive(cls, v: list[float]) -> list[float]:
        """Reject any non-positive price before the calculation layer sees it."""
        for i, p in enumerate(v):
            if p <= 0:
                raise ValueError(
                    f"All prices must be positive; got {p} at index {i}"
                )
        return v


class RiskAnalysisResponse(BaseModel):
    """Response body for the /risk/analyse endpoint."""

    volatility: float = Field(
        ...,
        description="Annualised volatility (standard deviation of returns).",
    )
    var: float = Field(
        ...,
        description=(
            "Parametric (Gaussian) Value-at-Risk at the requested confidence "
            "level, expressed in the same units as portfolio_value."
        ),
    )
    sharpe_ratio: float = Field(
        ...,
        description="Annualised Sharpe ratio (excess return per unit of risk).",
    )
    max_drawdown: float = Field(
        ...,
        description="Maximum peak-to-trough drawdown as a positive decimal.",
    )
    recommendation: RiskRecommendation = Field(
        ...,
        description="Rule-based risk recommendation with explanations.",
    )


# ---------------------------------------------------------------------------
# Ticker Risk Analysis schemas
# ---------------------------------------------------------------------------

_VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"}


class TickerRiskRequest(BaseModel):
    """Request body for the POST /risk/analyse/ticker endpoint."""

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol, e.g. 'AAPL' or 'MSFT'.",
        examples=["AAPL"],
    )
    period: Optional[str] = Field(
        default="1y",
        description=(
            "yfinance period string. One of: "
            + ", ".join(sorted(_VALID_PERIODS))
            + ". Mutually exclusive with start/end."
        ),
    )
    start: Optional[date] = Field(
        default=None,
        description=(
            "Start date (YYYY-MM-DD) for the historical range. "
            "Mutually exclusive with period."
        ),
    )
    end: Optional[date] = Field(
        default=None,
        description="End date (YYYY-MM-DD, exclusive). Used only with start.",
    )
    confidence_level: float = Field(
        default=0.95,
        gt=0.0,
        lt=1.0,
        description="VaR confidence level in (0, 1).",
    )
    risk_free_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Annualised risk-free rate as a decimal.",
    )
    portfolio_value: float = Field(
        default=1.0,
        gt=0.0,
        description="Portfolio value used to scale VaR output.",
    )
    trading_days_per_year: int = Field(
        default=252,
        gt=0,
        description="Trading days per year used for annualisation.",
    )

    @field_validator("ticker")
    @classmethod
    def ticker_must_not_be_blank(cls, v: str) -> str:
        """Normalise and ensure the ticker is not whitespace-only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("ticker must not be blank")
        return stripped.upper()

    @field_validator("period")
    @classmethod
    def period_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Accept only the period strings that yfinance understands."""
        if v is not None and v not in _VALID_PERIODS:
            raise ValueError(
                f"period must be one of {sorted(_VALID_PERIODS)}, got '{v}'"
            )
        return v


class TickerRiskResponse(BaseModel):
    """Response body for the POST /risk/analyse/ticker endpoint."""

    ticker: str = Field(..., description="Normalised ticker symbol that was analysed.")
    period_used: str = Field(
        ...,
        description=(
            "Human-readable description of the date range actually used, "
            "e.g. 'period=1y' or 'start=2023-01-01 end=2023-12-31'."
        ),
    )
    num_prices: int = Field(
        ...,
        description="Number of closing-price data points retrieved.",
    )
    volatility: float = Field(..., description="Annualised volatility.")
    var: float = Field(..., description="Parametric Value-at-Risk.")
    sharpe_ratio: float = Field(..., description="Annualised Sharpe ratio.")
    max_drawdown: float = Field(..., description="Maximum peak-to-trough drawdown.")
    recommendation: RiskRecommendation = Field(
        ...,
        description="Rule-based risk recommendation with explanations.",
    )


# ---------------------------------------------------------------------------
# Prototype Financial Risk Indicator schemas
# ---------------------------------------------------------------------------


class FinancialRiskRequest(BaseModel):
    """Request body for the POST /risk/financial endpoint."""

    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the company being analysed.",
        examples=["Demo Manufacturing Ltd."],
    )
    current_revenue: float = Field(
        ...,
        description="Most recent period total revenue.",
        examples=[10_000_000.0],
    )
    previous_revenue: float = Field(
        ...,
        description="Prior period total revenue. Must not be zero.",
        examples=[10_800_000.0],
    )
    current_net_profit: float = Field(
        ...,
        description="Most recent period net profit (may be negative).",
        examples=[500_000.0],
    )
    previous_net_profit: float = Field(
        ...,
        description="Prior period net profit (may be negative, but must not be zero).",
        examples=[590_000.0],
    )
    total_debt: float = Field(
        ...,
        ge=0.0,
        description="Total outstanding debt (non-negative).",
        examples=[2_500_000.0],
    )
    shareholders_equity: float = Field(
        ...,
        description="Total shareholders' equity. Must not be zero.",
        examples=[1_000_000.0],
    )
    current_assets: float = Field(
        ...,
        ge=0.0,
        description="Total current assets (non-negative).",
        examples=[1_200_000.0],
    )
    current_liabilities: float = Field(
        ...,
        gt=0.0,
        description="Total current liabilities. Must be positive.",
        examples=[1_500_000.0],
    )

    @field_validator("previous_revenue")
    @classmethod
    def previous_revenue_nonzero(cls, v: float) -> float:
        """Previous revenue must not be zero (used as a denominator)."""
        if v == 0.0:
            raise ValueError("previous_revenue must not be zero.")
        return v

    @field_validator("previous_net_profit")
    @classmethod
    def previous_net_profit_nonzero(cls, v: float) -> float:
        """Previous net profit must not be zero (used as a denominator)."""
        if v == 0.0:
            raise ValueError("previous_net_profit must not be zero.")
        return v

    @field_validator("shareholders_equity")
    @classmethod
    def shareholders_equity_nonzero(cls, v: float) -> float:
        """Shareholders' equity must not be zero (used as a denominator)."""
        if v == 0.0:
            raise ValueError("shareholders_equity must not be zero.")
        return v

    @field_validator("current_revenue")
    @classmethod
    def current_revenue_nonzero(cls, v: float) -> float:
        """Current revenue must not be zero (used as a denominator for NPM)."""
        if v == 0.0:
            raise ValueError("current_revenue must not be zero.")
        return v


class MetricResultSchema(BaseModel):
    """A single computed financial metric with its prototype risk classification."""

    name: str
    value: float
    formatted_value: str
    level: str
    explanation: str
    threshold_note: str


class FinancialRiskResponse(BaseModel):
    """Response body for the POST /risk/financial endpoint."""

    company_name: str
    overall_risk: str = Field(
        ...,
        description="Prototype Financial Risk Indicator: LOW, MODERATE, or HIGH.",
    )
    overall_explanation: str
    metrics: list[MetricResultSchema]
    current_revenue: float
    previous_revenue: float
    current_net_profit: float
    previous_net_profit: float
