"""
FinRisk AI — FastAPI application entry point.

Start the development server with:
    uvicorn backend.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.risk import router as risk_router
from backend.db.session import engine
from backend.models.orm import Base
from backend.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    On startup: create all database tables that do not yet exist.
    On shutdown: nothing special is needed for SQLite.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FinRisk AI",
    version="0.1.0",
    description="Financial risk analysis and prediction MVP.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "https://tourmaline-marzipan-02a9ad.netlify.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(risk_router)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health_check() -> HealthResponse:
    """Return the application health status."""
    return HealthResponse(status="ok")
