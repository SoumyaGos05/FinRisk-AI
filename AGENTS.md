# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

FinRisk AI is a beginner-friendly financial risk analysis and prediction MVP. The project is split into a Python/FastAPI backend and a React/Vite frontend that communicate over REST.

## Directory Structure

```
finrisk-ai/
├── backend/
│   ├── api/          # FastAPI route handlers (one file per domain)
│   ├── logic/        # Financial risk and business logic
│   ├── data/         # Data ingestion and processing (yfinance, pandas)
│   ├── models/       # SQLAlchemy ORM models + Pydantic schemas
│   ├── ml/           # Scikit-learn risk/prediction models
│   ├── db/           # Database session factory and migrations
│   ├── config.py     # Settings loaded from .env via python-dotenv
│   └── main.py       # FastAPI app entry point
├── tests/            # pytest test suite (mirrors backend/ structure)
├── frontend/         # React + Vite app
│   ├── src/
│   └── index.html
├── .env              # Local secrets — NEVER commit (in .gitignore)
├── .env.example      # Committed template with placeholder values
├── requirements.txt
└── README.md
```

## Commands

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server (auto-reload)
uvicorn backend.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_risk_logic.py

# Run a single test by name
pytest tests/test_risk_logic.py::test_var_calculation

# Run tests with output
pytest -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # Vite dev server (http://localhost:5173)
npm run build     # Production build
npm run preview   # Preview production build
```

## Code Style

- **Python**: PEP 8. Use `snake_case` for variables/functions, `PascalCase` for classes.
- **Type hints**: Required on all function signatures. Use `Optional[X]` and `list[X]` (Python 3.9+ generics).
- **Docstrings**: Required on all public functions and classes. Single-line for simple helpers, multi-line for anything non-trivial.
- **Pydantic models** define both request/response schemas and input validation — do not use raw `dict` in route handlers.
- **SQLAlchemy models** live in `backend/models/`. Keep ORM models separate from Pydantic schemas.
- **Database access**: Always go through the session factory in `backend/db/`. Do not import `engine` directly in route handlers — use dependency injection (`Depends(get_db)`).
- **Config/secrets**: Read all settings through `backend/config.py` (a `pydantic-settings` or `python-dotenv` `Settings` class). Never read `os.environ` directly outside `config.py`.

## ML / Data Rules

- Start with statistical/explainable models (e.g., VaR, volatility, linear regression) before reaching for more complex ML.
- Scikit-learn pipelines preferred for any trained model so preprocessing and inference stay coupled.
- Use `yfinance` only when live market data is genuinely needed; mock or cache responses in tests.
- Do **not** add PyTorch, LangChain, LlamaIndex, or similar heavy frameworks without an explicit requirement.

## Testing

- Tests mirror the `backend/` directory structure under `tests/`.
- Each layer (API, logic, data, ml) has its own test file.
- Mock external calls (`yfinance`, HTTP) with `pytest-mock` or `unittest.mock` — tests must run fully offline.
- API tests use FastAPI's `TestClient` (no running server needed).
- Keep each component independently testable; avoid cross-layer imports in tests.

## Critical Constraints

- **SQLite for MVP**: Database URL comes from `.env`. Keep `db/` layer abstract enough (session factory, repository pattern) so switching to PostgreSQL later requires only a URL change and possibly a driver swap.
- **No microservices, no Kubernetes, no paid APIs**: All infrastructure must be free and local.
- **Frontend ↔ Backend**: Frontend only communicates via the FastAPI REST API. No direct DB access from the frontend.
- **Incremental builds**: Each new feature should leave all existing tests green. Add tests alongside new logic.
