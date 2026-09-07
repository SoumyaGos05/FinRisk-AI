# FinRisk AI

A beginner-friendly financial risk analysis and prediction MVP.

- **Backend**: Python 3.11 · FastAPI · SQLAlchemy · SQLite
- **Frontend**: React · Vite
- **Tests**: pytest

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11 |
| Node.js | 18 |
| npm | 9 |

---

## Backend Setup

```bash
# 1. Create a project-local virtual environment
python -m venv .venv

# 2. Activate it
#    Windows:
.venv\Scripts\activate
#    macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 4. Create your local .env file (already pre-filled for SQLite)
cp .env.example .env
```

---

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

---

## Running the App

Open **two terminals**.

**Terminal 1 — Backend** (from the project root, with `.venv` activated):

```bash
uvicorn backend.main:app --reload
```

The API will be available at <http://localhost:8000>.  
Interactive docs: <http://localhost:8000/docs>

**Terminal 2 — Frontend** (from the `frontend/` directory):

```bash
npm run dev
```

The UI will be available at <http://localhost:5173>.

---

## Running Tests

All commands run from the project root with `.venv` activated.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a single test file
pytest tests/test_api.py

# Run a single test by name
pytest tests/test_api.py::test_health_endpoint -v
```

---

## Project Structure

```
finrisk-ai/
├── backend/
│   ├── api/          # FastAPI route handlers (one file per domain)
│   ├── config.py     # Settings loaded from .env — the only place os.environ is read
│   ├── data/         # Data ingestion and processing
│   ├── db/
│   │   └── session.py  # SQLAlchemy engine, SessionLocal, get_db dependency
│   ├── logic/        # Financial risk and business logic (pure Python, no DB/HTTP)
│   ├── main.py       # FastAPI app entry point
│   ├── ml/           # Scikit-learn risk/prediction models
│   └── models/
│       ├── orm.py      # SQLAlchemy ORM table definitions
│       └── schemas.py  # Pydantic request/response schemas
├── frontend/
│   ├── src/
│   │   ├── api.js    # Central API base URL (reads VITE_API_BASE_URL)
│   │   └── App.jsx   # Root React component
│   └── .env.example
├── tests/
│   ├── conftest.py   # Shared fixtures (TestClient, in-memory DB override)
│   ├── test_api.py   # API endpoint tests
│   └── test_config.py
├── .env.example      # Template — copy to .env and fill in values
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
└── README.md         # This file
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./finrisk.db` |
| `APP_ENV` | Runtime environment | `development` |

> **Never commit `.env`** — it is listed in `.gitignore`.

---

## Adding a New Feature

1. Add business logic to `backend/logic/` (pure Python, no DB/HTTP).
2. Add a route in `backend/api/` using `Depends(get_db)` for database access.
3. Add Pydantic schemas to `backend/models/schemas.py`.
4. Add ORM models to `backend/models/orm.py` if a new table is needed.
5. Add a corresponding test file in `tests/`.
6. Run `pytest -v` and confirm all tests are green before committing.
