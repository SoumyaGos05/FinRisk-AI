# FinRisk AI — MVP Skeleton Plan

## Overview

Build the complete project skeleton for FinRisk AI: a Python/FastAPI backend with SQLite/SQLAlchemy,
a React/Vite frontend, configuration handling, pytest infrastructure, and supporting files
(requirements, .gitignore, README, .env.example).

No financial logic, ML models, authentication, or advanced features are implemented in this step.
Every file created here must pass lint/import checks and the initial pytest suite must be green.

## Confirmed Decisions

- **Virtual environment**: Create and use a project-local `.venv` at the repository root.
  All `pip` and `pytest` commands use `.venv/Scripts/python` (Windows) or `.venv/bin/python` (Unix).
  The system/global Python is never used for project dependencies.
- **Frontend scaffolding**: Use `npm create vite@latest frontend -- --template react` (Node.js and
  npm are confirmed available on the machine).
- **No ML/data packages**: pandas, NumPy, scikit-learn, yfinance, LangChain, LlamaIndex, and all
  other AI/ML frameworks are explicitly excluded from this step. They will be introduced when the
  financial risk engine is implemented.
- **No financial logic**: Zero risk calculations, model training, or domain logic in this step.

---

## Sub-Task 1 — Configuration and environment handling

**Status:** [x] done

**Intent:**
Establish `backend/config.py` as the single source of truth for all settings read from `.env`.
Also create `.env.example` and `.env` (gitignored) so the app can boot.

**Expected Outcomes:**
- `backend/config.py` exports a `Settings` Pydantic model and a `settings` singleton.
- `DATABASE_URL` and `APP_ENV` are the only variables needed at this stage.
- `.env.example` is committed; `.env` is not.

**Todo List:**
1. Create `backend/__init__.py` (empty).
2. Create `backend/config.py` using `pydantic-settings` `BaseSettings` to load `.env`.
   Fields: `DATABASE_URL: str`, `APP_ENV: str = "development"`.
3. Create `.env.example` with placeholder values for every field in `Settings`.
4. Create `.env` (local only) with concrete SQLite URL: `sqlite:///./finrisk.db`.

**Relevant Context:**
- `.bob/rules-agent/AGENTS.md` §Config and Secrets: only `config.py` may read `os.environ`.
- `AGENTS.md` §Critical Constraints: `DATABASE_URL` is the single change-point for SQLite→PostgreSQL.

---

## Sub-Task 2 — SQLAlchemy database foundation

**Status:** [x] done

**Intent:**
Create the session factory, base declarative model, and `get_db` dependency.
No ORM model tables are defined yet — just the engine wiring.

**Expected Outcomes:**
- `backend/db/__init__.py` and `backend/db/session.py` exist.
- `get_db()` is a proper generator that yields a session and closes it on exit.
- `backend/models/__init__.py` and `backend/models/orm.py` exist with only `Base = declarative_base()`.
- `create_all()` is called from `main.py` startup (not from `db/session.py`).

**Todo List:**
1. Create `backend/db/__init__.py` (empty).
2. Create `backend/db/session.py`:
   - Import `settings` from `backend/config.py`.
   - Create `engine` via `create_engine(settings.DATABASE_URL, ...)`.
   - Create `SessionLocal = sessionmaker(...)`.
   - Define `get_db()` generator.
3. Create `backend/models/__init__.py` (empty).
4. Create `backend/models/orm.py` with `Base = declarative_base()` only.

**Relevant Context:**
- `.bob/rules-agent/AGENTS.md` §Database Layer: session factory must be backend-agnostic.
- Routes must use `Depends(get_db)` — never import `SessionLocal` directly in routes.

---

## Sub-Task 3 — FastAPI application entry point

**Status:** [x] done

**Intent:**
Wire up `backend/main.py` as the ASGI application: create the `FastAPI` instance,
attach a health-check route, and call `Base.metadata.create_all` on startup.
No domain routes yet.

**Expected Outcomes:**
- `uvicorn backend.main:app --reload` starts without error.
- `GET /health` returns `{"status": "ok"}` with a Pydantic response model.
- `backend/api/__init__.py` exists (empty placeholder for future routers).

**Todo List:**
1. Create `backend/api/__init__.py` (empty).
2. Create `backend/main.py`:
   - Instantiate `FastAPI(title="FinRisk AI", version="0.1.0")`.
   - Add `@app.on_event("startup")` handler that calls `Base.metadata.create_all(bind=engine)`.
   - Define a `HealthResponse` Pydantic schema inline (or import from a schemas file).
   - Add `GET /health` returning `HealthResponse`.
3. Create stub package `__init__.py` files for `backend/logic/`, `backend/data/`, `backend/ml/`.

**Relevant Context:**
- `.bob/rules-agent/AGENTS.md` §FastAPI Route Handlers: every endpoint needs `response_model=`.
- Layer boundary: `main.py` may import from `db/` and `models/` but not from `logic/` or `ml/`.

---

## Sub-Task 4 — Pydantic schemas placeholder

**Status:** [x] done

**Intent:**
Create `backend/models/schemas.py` with only a shared `HealthResponse` schema used by the health
endpoint. Establishes the ORM-vs-schema separation from day one.

**Expected Outcomes:**
- `backend/models/schemas.py` exists and exports `HealthResponse`.
- `backend/main.py` imports `HealthResponse` from `backend/models/schemas` (not defined inline).

**Todo List:**
1. Create `backend/models/schemas.py` with `class HealthResponse(BaseModel): status: str`.
2. Update `backend/main.py` to import `HealthResponse` from `backend/models/schemas`.

**Relevant Context:**
- `AGENTS.md` §Code Style: ORM models and Pydantic schemas are separate files within `backend/models/`.

---

## Sub-Task 5 — pytest infrastructure

**Status:** [x] done

**Intent:**
Set up the test directory structure mirroring `backend/`, a `conftest.py` with a `TestClient`
fixture and an in-memory SQLite override, and two initial test files that verify the health
endpoint and that imports resolve cleanly.

**Expected Outcomes:**
- `tests/` directory with `__init__.py`, `conftest.py`, `test_api.py`, `test_config.py`.
- `pytest` (no arguments) exits green.
- `test_api.py` tests `GET /health` via `TestClient`.
- `test_config.py` tests that `settings.DATABASE_URL` is not empty.

**Todo List:**
1. Create `tests/__init__.py` (empty).
2. Create `tests/conftest.py`:
   - Override `DATABASE_URL` to `sqlite:///./test.db` (or in-memory `sqlite:///:memory:`).
   - Provide a `client` fixture using `TestClient(app)`.
3. Create `tests/test_api.py` with `test_health_endpoint` using the `client` fixture.
4. Create `tests/test_config.py` with `test_settings_load` asserting `settings.DATABASE_URL` is set.

**Relevant Context:**
- `AGENTS.md` §Testing: API tests use `TestClient`; tests run fully offline.
- `.bob/rules-agent/AGENTS.md` §Testing: `TestClient` from `fastapi.testclient`, not a live server.

---

## Sub-Task 6 — Frontend skeleton (React + Vite)

**Status:** [x] done

**Intent:**
Scaffold a minimal Vite + React frontend under `frontend/`. The only project-specific rule
is that the API base URL comes from `VITE_API_BASE_URL` (never hardcoded).

**Expected Outcomes:**
- `frontend/` contains a working Vite + React app (`npm run dev` starts without error).
- `frontend/.env.example` has `VITE_API_BASE_URL=http://localhost:8000`.
- `frontend/src/api.js` exports a single `apiBase` constant sourced from `import.meta.env.VITE_API_BASE_URL`.
- App displays a minimal "FinRisk AI" heading with no errors in the browser console.

**Todo List:**
1. Scaffold with `npm create vite@latest frontend -- --template react` (Node.js/npm confirmed available).
2. Run `npm install` inside `frontend/`.
3. Add `frontend/.env.example` with `VITE_API_BASE_URL=http://localhost:8000`.
4. Add `frontend/.env` (gitignored) with the same value for local dev.
5. Create `frontend/src/api.js` exporting `export const apiBase = import.meta.env.VITE_API_BASE_URL`.
6. Simplify `frontend/src/App.jsx` to a single `<h1>FinRisk AI</h1>` placeholder.
7. Confirm `npm run build` exits clean (no type/lint errors in the scaffold).

**Relevant Context:**
- `.bob/rules-agent/AGENTS.md` §Frontend: `VITE_API_BASE_URL` is mandatory; no hardcoded localhost.

---

## Sub-Task 7 — requirements.txt and dependency files

**Status:** [x] done

**Intent:**
Pin the exact packages needed for the skeleton. No ML packages yet — they are added per feature.

**Expected Outcomes:**
- `requirements.txt` lists only packages actually imported by the skeleton code.
- A `requirements-dev.txt` (or `[dev]` extras) covers pytest and test utilities.

**Packages for `requirements.txt`:**
```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
python-dotenv
```

**Packages for `requirements-dev.txt`:**
```
pytest
pytest-mock
httpx          # required by TestClient in newer FastAPI versions
```

**Explicitly excluded (added in later feature steps only):**
- pandas, numpy, scikit-learn, yfinance, torch, langchain, llama-index

**Todo List:**
1. Create `requirements.txt` with the packages above (no version pins for MVP — add pins when stabilising).
2. Create `requirements-dev.txt` with test/dev packages.

**Relevant Context:**
- `AGENTS.md` §Critical Constraints: Do not add packages not required for this foundation.
- pandas, numpy, scikit-learn, yfinance are NOT included yet — confirmed by user decision.

---

## Sub-Task 8 — .gitignore

**Status:** [x] done

**Intent:**
Protect secrets, generated artefacts, and environment-specific files from being committed.

**Expected Outcomes:**
- `.env` is in `.gitignore` (both root `.env` and `frontend/.env`).
- `*.joblib` and `backend/ml/artefacts/` are in `.gitignore`.
- `.venv/` is in `.gitignore` (project-local virtual environment must not be committed).
- Standard Python (`__pycache__`, `.venv`, `*.pyc`, `*.egg-info`) and Node (`node_modules`, `dist`) patterns included.
- `finrisk.db` and `test.db` are gitignored.

**Todo List:**
1. Create `.gitignore` with all patterns listed above.

---

## Sub-Task 9 — README.md

**Status:** [x] done

**Intent:**
Document exact setup, run, and test commands so a beginner can get from zero to running in one read.

**Expected Outcomes:**
- README covers: prerequisites, backend setup, frontend setup, running the dev servers,
  running tests (all tests and a single test), and project structure overview.
- All commands are exact copy-paste (no placeholders).

**Todo List:**
1. Create `README.md` with sections: Prerequisites, Backend Setup, Frontend Setup,
   Running the App, Running Tests, Project Structure.

---

## Verification (runs after all sub-tasks)

After all files are created, the implementing agent must execute the following using the
project-local `.venv` — never the global Python:

1. Create `.venv`:
   ```
   python -m venv .venv
   ```
2. Install dependencies into `.venv`:
   ```
   .venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt   # Windows
   # or
   .venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt        # Unix/macOS
   ```
3. Run tests:
   ```
   .venv\Scripts\pytest -v      # Windows
   # or
   .venv/bin/pytest -v           # Unix/macOS
   ```
   Confirm: zero failures, zero errors.
4. Smoke-test the server (start, check output, stop):
   ```
   .venv\Scripts\uvicorn backend.main:app   # Windows — start then Ctrl+C
   ```
5. Verify frontend build:
   ```
   cd frontend && npm run build
   ```
6. Report: files created, commands executed, full pytest output, any warnings or errors.
