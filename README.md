# FinRisk AI

**AI-Assisted Financial Risk Analysis & Sustainable Decision Support**

FinRisk AI is a web-based financial risk analysis and decision-support MVP. It evaluates key financial indicators using a deterministic Python risk engine and provides a natural-language explanation of the calculated result using Google Gemini.

The system is designed to make financial risk information easier to understand while keeping human judgment involved in consequential financial decisions.

---

## Features

* Company/ticker-based financial analysis
* Financial data retrieval using **yfinance**
* Deterministic financial risk calculation using Python
* Threshold-based **LOW / MODERATE / HIGH** risk classification
* Analysis of multiple financial indicators:

  * Revenue Growth
  * Profit Growth
  * Debt-to-Equity Ratio
  * Current Ratio
  * Net Profit Margin
* Natural-language result explanation using **Google Gemini**
* React-based web dashboard
* FastAPI backend
* Automated backend tests using pytest
* Responsible AI disclaimer for financial decision support
* Frontend deployment through Netlify
* Backend/API deployment through Render

### Important AI distinction

The risk classification is performed by the **deterministic Python risk engine** using predefined thresholds.

**Google Gemini does not independently determine the risk level.** It is used to explain the already-calculated result in natural language.

**IBM Bob** was used as development/coding assistance during implementation. It is not the financial risk engine or the AI model used for explanations.

---

## Technology Stack

| Component              | Technology                       |
| ---------------------- | -------------------------------- |
| Backend                | Python · FastAPI                 |
| Frontend               | React · Vite                     |
| Financial Data         | yfinance                         |
| Risk Analysis          | Python deterministic risk engine |
| AI Explanation         | Google Gemini API                |
| Database               | SQLite · SQLAlchemy              |
| Testing                | pytest                           |
| Development Assistance | IBM Bob                          |
| Frontend Deployment    | Netlify                          |
| Backend/API Deployment | Render                           |

---

## Prerequisites

| Tool    | Minimum Version |
| ------- | --------------- |
| Python  | 3.11            |
| Node.js | 18              |
| npm     | 9               |

---

## System Workflow

The application follows this general workflow:

```text
Company / Ticker Input
        ↓
React + Vite Frontend
        ↓
FastAPI + Python Backend
        ↓
Financial Data via yfinance
        ↓
Deterministic Risk Engine
        ↓
Financial Metrics
        ↓
Predefined Threshold Evaluation
        ↓
LOW / MODERATE / HIGH
        ↓
Google Gemini Explanation
        ↓
Risk Dashboard
```

The calculation and AI explanation stages are intentionally separated to make the system easier to understand and review.

---

## Financial Indicators

FinRisk AI currently evaluates the following indicators:

### 1. Revenue Growth

Measures the change in company revenue over the available financial periods.

### 2. Profit Growth

Measures the change in company profit over the available financial periods.

### 3. Debt-to-Equity Ratio

Provides an indication of the company's leverage relative to shareholder equity.

### 4. Current Ratio

Provides an indication of the company's short-term liquidity position.

### 5. Net Profit Margin

Measures the proportion of revenue retained as net profit.

These indicators are evaluated using predefined thresholds to produce the overall risk classification.

---

## Risk Classification

The current prototype uses deterministic threshold-based logic.

The overall result is classified as:

```text
LOW RISK
MODERATE RISK
HIGH RISK
```

The risk engine is implemented in Python and does not rely on Gemini to decide the classification.

Gemini is used after classification to provide a human-readable explanation of the result and the underlying financial indicators.

---

## Responsible AI

FinRisk AI is designed as an analytical and explanatory prototype.

The system does not replace professional financial analysis or human judgment.

Important principles include:

* **Transparency:** The main risk classification is based on predefined financial rules and thresholds.
* **Explainability:** Gemini provides a natural-language explanation of the calculated result.
* **Human Oversight:** Users remain responsible for reviewing and interpreting the information.
* **Responsible Use:** The output should not be treated as guaranteed financial advice or an autonomous financial decision.
* **Privacy:** Sensitive credentials and environment variables are kept outside the committed source code.

> **Disclaimer:** AI-generated explanations are provided for informational purposes and should not replace independent or professional financial judgment for consequential decisions.

---

## Sustainability Context

FinRisk AI is a finance-focused project developed under the **1M1B AI for Sustainability Virtual Internship**.

The project's sustainability relevance is focused on supporting more responsible and informed financial decision-making.

The project is primarily aligned with:

**SDG 12 — Responsible Consumption and Production**

The current prototype does **not** calculate carbon emissions, environmental impact, ESG scores, or other environmental measurements.

---

## Backend Setup

From the project root:

### 1. Create a project-local virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 4. Create the local environment file

**Windows Command Prompt:**

```bash
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Configure the required environment variables in `.env` as needed.

**Never commit `.env` to Git.**

---

## Frontend Setup

From the project root:

```bash
cd frontend
npm install
```

Create the local frontend environment file from the provided example.

**Windows Command Prompt:**

```bash
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

The frontend API configuration uses:

```text
VITE_API_BASE_URL
```

---

## Running the Application Locally

Open two terminals.

### Terminal 1 — Backend

From the project root, with the virtual environment activated:

```bash
uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### Terminal 2 — Frontend

From the `frontend/` directory:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## Running Tests

All tests can be run from the project root with the virtual environment activated.

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_api.py
```

### Run a specific test

```bash
pytest tests/test_api.py::test_health_endpoint -v
```

The project has been tested with the backend test suite during development.

---

## Deployment

### Frontend

The frontend is deployed using **Netlify**.

**Live Application:**

https://finriskai.netlify.app/

### Backend

The FastAPI backend/API is deployed separately using **Render**.

The frontend communicates with the deployed backend through the configured API base URL.

> Deployment availability depends on the respective hosting services and their current runtime status.

---

## Project Structure

```text
finrisk-ai/
├── backend/
│   ├── api/                 # FastAPI route handlers
│   ├── config.py            # Application configuration and environment settings
│   ├── data/                # Financial data ingestion and processing
│   ├── db/
│   │   └── session.py       # Database engine and session management
│   ├── logic/               # Financial risk and business logic
│   │   ├── risk_engine.py   # Deterministic financial risk calculations
│   │   └── recommender.py   # Risk classification/recommendation logic
│   ├── main.py              # FastAPI application entry point
│   └── models/
│       ├── orm.py           # SQLAlchemy ORM definitions
│       └── schemas.py       # Pydantic request/response schemas
│
├── frontend/
│   ├── src/
│   │   ├── api.js           # Central API configuration
│   │   ├── components/
│   │   │   └── RiskDashboard.jsx
│   │   └── App.jsx          # Root React component
│   └── .env.example
│
├── tests/
│   ├── conftest.py          # Shared test fixtures
│   ├── test_api.py          # API endpoint tests
│   └── test_config.py       # Configuration tests
│
├── .env.example             # Environment variable template
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Environment Variables

Environment variables are used for local configuration and secrets.

| Variable            | Description                          |
| ------------------- | ------------------------------------ |
| `DATABASE_URL`      | SQLAlchemy database connection URL   |
| `APP_ENV`           | Application runtime environment      |
| `VITE_API_BASE_URL` | Backend API URL used by the frontend |
| `GEMINI_API_KEY`    | Google Gemini API key                |

The exact variables required may depend on the configured local/deployment environment.

> **Never commit `.env` files or API keys to Git.** They are excluded through `.gitignore`.

---

## Development Guidelines

When adding a new feature:

1. Add business logic to `backend/logic/` where appropriate.
2. Keep financial calculations independent from HTTP and database concerns where possible.
3. Add API routes in `backend/api/`.
4. Use the existing database dependency pattern where database access is required.
5. Add or update Pydantic schemas in `backend/models/schemas.py`.
6. Add or update ORM models only when a database table is required.
7. Add corresponding tests.
8. Run the test suite before committing changes.

---

## Current Scope

The current MVP focuses on:

* Financial data retrieval
* Financial indicator calculation
* Rule/threshold-based risk classification
* AI-assisted explanation
* Web-based presentation of results
* Responsible financial decision support

The project is intended as a working prototype rather than a production banking, investment-management, or enterprise risk platform.

---

## Future Scope

Potential future improvements include:

* ML-based risk prediction using suitable historical datasets
* Financial trend and anomaly analysis
* Sector benchmarking
* Scenario analysis
* Early-warning monitoring
* Expanded sustainability-related financial indicators

These are **future enhancements and are not part of the current MVP**.

---

## Limitations

The current prototype has several limitations:

* Risk classification depends on predefined thresholds.
* Financial data availability depends on the selected data source.
* AI-generated explanations may require human review.
* The system is not intended to provide guaranteed investment or lending decisions.
* The current prototype does not provide ESG or environmental scoring.
* Future machine-learning capabilities would require suitable historical datasets and additional validation.

---

## Project Context

FinRisk AI was developed as part of the:

**1M1B AI for Sustainability Virtual Internship**

in collaboration with:

* **IBM SkillsBuild**
* **AICTE**

The project demonstrates how AI-assisted explanations can be combined with transparent rule-based financial analysis to support more understandable and responsible financial decision-making.

---

## License

This project is intended as an academic/internship prototype.
