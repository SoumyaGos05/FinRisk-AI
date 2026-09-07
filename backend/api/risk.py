"""
FastAPI router for risk-analysis endpoints.

All calculation logic is delegated to ``backend.logic.risk_engine`` and
``backend.logic.financial_metrics`` — this module handles only HTTP concerns
(routing, request/response serialisation, and error translation).
"""

from fastapi import APIRouter, HTTPException

from backend.data.market import MarketDataError, fetch_closing_prices
from backend.logic.financial_metrics import analyse_financial_risk
from backend.logic.recommender import generate_recommendation
from backend.logic.risk_engine import analyse_risk
from backend.models.schemas import (
    FinancialRiskRequest,
    FinancialRiskResponse,
    MetricResultSchema,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    TickerRiskRequest,
    TickerRiskResponse,
)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post(
    "/analyse",
    response_model=RiskAnalysisResponse,
    summary="Analyse portfolio risk",
    description=(
        "Compute annualised volatility, parametric Value-at-Risk, Sharpe ratio, "
        "and maximum drawdown from an ordered list of asset prices."
    ),
)
def analyse_risk_endpoint(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """
    Compute financial risk metrics from a price series.

    Delegates all calculation to the pure-Python risk engine and maps any
    ``ValueError`` from bad inputs to a 422 Unprocessable Entity response.
    """
    try:
        metrics = analyse_risk(
            prices=request.prices,
            confidence_level=request.confidence_level,
            risk_free_rate=request.risk_free_rate,
            portfolio_value=request.portfolio_value,
            trading_days_per_year=request.trading_days_per_year,
        )
    except ValueError as exc:
        # Should rarely fire because Pydantic validates most constraints,
        # but acts as a safety net for any edge-cases that slip through.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    recommendation = generate_recommendation(
        volatility=metrics["volatility"],
        var=metrics["var"],
        sharpe_ratio=metrics["sharpe_ratio"],
        max_drawdown=metrics["max_drawdown"],
        portfolio_value=request.portfolio_value,
    )
    return RiskAnalysisResponse(**metrics, recommendation=recommendation)


@router.post(
    "/analyse/ticker",
    response_model=TickerRiskResponse,
    summary="Analyse risk for a stock ticker",
    description=(
        "Fetch historical closing prices from Yahoo Finance for the given ticker "
        "and compute annualised volatility, parametric Value-at-Risk, Sharpe ratio, "
        "and maximum drawdown."
    ),
)
def analyse_ticker_endpoint(request: TickerRiskRequest) -> TickerRiskResponse:
    """
    Fetch market data for *ticker* then run the risk engine.

    - Supply ``period`` (e.g. ``"1y"``) **or** ``start`` (with optional ``end``).
    - When both ``period`` and ``start`` are omitted, defaults to ``period="1y"``.
    - Returns 422 for invalid inputs, 502 when Yahoo Finance cannot be reached
      or returns no data.
    """
    # Resolve period vs date-range — Pydantic default leaves period="1y" when
    # neither start nor end is provided; reject the ambiguous case where the
    # caller supplies both.
    if request.start is not None and request.period is not None:
        raise HTTPException(
            status_code=422,
            detail="Supply either 'period' or 'start'/'end', not both.",
        )

    # Build a human-readable label for the response.
    if request.start is not None:
        period_used = f"start={request.start}"
        if request.end is not None:
            period_used += f" end={request.end}"
    else:
        period_used = f"period={request.period}"

    try:
        prices = fetch_closing_prices(
            ticker=request.ticker,
            period=request.period if request.start is None else None,
            start=request.start,
            end=request.end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        metrics = analyse_risk(
            prices=prices,
            confidence_level=request.confidence_level,
            risk_free_rate=request.risk_free_rate,
            portfolio_value=request.portfolio_value,
            trading_days_per_year=request.trading_days_per_year,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    recommendation = generate_recommendation(
        volatility=metrics["volatility"],
        var=metrics["var"],
        sharpe_ratio=metrics["sharpe_ratio"],
        max_drawdown=metrics["max_drawdown"],
        portfolio_value=request.portfolio_value,
    )
    return TickerRiskResponse(
        ticker=request.ticker,
        period_used=period_used,
        num_prices=len(prices),
        **metrics,
        recommendation=recommendation,
    )


@router.post(
    "/financial",
    response_model=FinancialRiskResponse,
    summary="Prototype Financial Risk Indicator",
    description=(
        "Compute the Prototype Financial Risk Indicator from a company's basic "
        "financial information.  All five metrics and the overall classification "
        "are calculated deterministically — no AI involvement in the numbers."
    ),
)
def financial_risk_endpoint(request: FinancialRiskRequest) -> FinancialRiskResponse:
    """
    Compute the Prototype Financial Risk Indicator.

    Delegates all calculation to ``backend.logic.financial_metrics`` and maps
    any ``ValueError`` from bad inputs to a 422 Unprocessable Entity response.
    """
    try:
        result = analyse_financial_risk(
            company_name=request.company_name,
            current_revenue=request.current_revenue,
            previous_revenue=request.previous_revenue,
            current_net_profit=request.current_net_profit,
            previous_net_profit=request.previous_net_profit,
            total_debt=request.total_debt,
            shareholders_equity=request.shareholders_equity,
            current_assets=request.current_assets,
            current_liabilities=request.current_liabilities,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return FinancialRiskResponse(
        company_name=result.company_name,
        overall_risk=result.overall_risk,
        overall_explanation=result.overall_explanation,
        metrics=[
            MetricResultSchema(
                name=m.name,
                value=m.value,
                formatted_value=m.formatted_value,
                level=m.level,
                explanation=m.explanation,
                threshold_note=m.threshold_note,
            )
            for m in result.metrics
        ],
        current_revenue=result.current_revenue,
        previous_revenue=result.previous_revenue,
        current_net_profit=result.current_net_profit,
        previous_net_profit=result.previous_net_profit,
    )
