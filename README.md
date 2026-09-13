# FinRisk AI

### AI-Assisted Financial Risk Analysis & Sustainable Decision Support

FinRisk AI is a web-based financial risk analysis application that evaluates a company's financial indicators and classifies its overall financial risk as **LOW, MODERATE, or HIGH**.

The project combines a **deterministic Python risk engine** with **Google Gemini** as an AI explanation layer. The risk calculation is performed using predefined financial rules and thresholds, while Gemini explains the already-calculated results in simple language.

> **Important:** Gemini does not calculate or override the financial risk classification. It only provides an explanatory summary of the deterministic analysis.

---

## Features

* Financial risk analysis from company financial data
* Revenue Growth analysis
* Profit Growth analysis
* Debt-to-Equity Ratio analysis
* Current Ratio analysis
* Net Profit Margin analysis
* Overall risk classification:

  * LOW
  * MODERATE
  * HIGH
* AI-generated explanation using Google Gemini
* Deterministic risk calculation independent of the AI provider
* Graceful fallback when Gemini is unavailable
* In-memory caching for repeated AI explanations
* Financial data retrieval using `yfinance`
* React-based web dashboard
* FastAPI backend
* SQLite database with SQLAlchemy
* Automated backend tests
* Deployed frontend and backend architecture

---

## How the AI Works

FinRisk AI uses two separate layers:

### 1. Deterministic Risk Engine

The Python risk engine calculates the financial indicators and determines the overall risk classification using predefined rules and thresholds.

The current indicators are:

| Indicator         | Purpose                                      |
| ----------------- | -------------------------------------------- |
| Revenue Growth    | Measures change in company revenue           |
| Profit Growth     | Measures change in company profit            |
| Debt-to-Equity    | Indicates relative debt compared with equity |
| Current Ratio     | Indicates short-term liquidity               |
| Net Profit Margin | Measures profitability relative to revenue   |

The system combines these results to produce an overall:

**LOW / MODERATE / HIGH** risk classification.

### 2. Gemini Explanation Layer

After the deterministic analysis is completed, Google Gemini receives the calculated results and produces a short natural-language explanation.

Gemini is instructed to:

* Use only the supplied financial values
* Not recalculate financial metrics
* Not invent financial values
* Not change the risk classification
* Not provide professional financial advice
* Recommend human/professional review for consequential decisions

If Gemini is unavailable, the deterministic financial analysis can still be returned.

---

## System Workflow

```text
Company / Financial Data
        ↓
Financial Data Processing
        ↓
Deterministic Risk Engine
        ↓
Financial Metrics
        ↓
LOW / MODERATE / HIGH Risk Classification
        ↓
AI Explanation Controller
        ↓
Google Gemini
        ↓
Short Natural-Language Explanation
        ↓
React Dashboard
```

The AI explanation is therefore an **additional interpretation layer**, not the source of the risk classification.

---

## Technology Stack

### Frontend

* React
* Vite
* JavaScript
* CSS

### Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic

### Financial Data

* `yfinance`

### AI

* Google Gemini API
* Direct REST integration using `httpx`

### Testing

* pytest

### Development Assistance

* IBM Bob

### Deployment

* Netlify — Frontend
* Render — Backend/API

---

## Project Structure

```text
FinRisk AI/
│
├── backend/
│   ├── ai/
│   │   ├── controller.py
│   │   ├── gemini.py
│   │   ├── provider.py
│   │   └── __init__.py
│   │
│   ├── api/
│   │   └── ...
│   │
│   ├── config.py
│   │
│   ├── data/
│   │   └── ...
│   │
│   ├── db/
│   │   └── ...
│   │
│   ├── logic/
│   │   ├── risk_engine.py
│   │   └── recommender.py
│   │
│   ├── models/
│   │   └── ...
│   │
│   ├── main.py
│   └── __init__.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RiskDashboard.jsx
│   │   │   └── RiskDashboard.css
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Backend AI Architecture

The AI integration is separated into three components:

### `backend/ai/controller.py`

Acts as the gateway between the API and the AI provider.

It:

* Creates a fingerprint of the calculated financial results
* Checks the in-memory cache
* Limits provider calls
* Calls Gemini when necessary
* Stores successful explanations
* Handles provider failures
* Allows the deterministic analysis to continue if AI is unavailable

### `backend/ai/gemini.py`

Contains the Google Gemini provider implementation.

The application communicates with Gemini through its REST API using `httpx`, without requiring a Google SDK.

### `backend/ai/provider.py`

Defines the common AI provider interface and provider-level error handling.

This keeps the AI layer separate from the financial calculation logic.

---

## Financial Risk Indicators

### Revenue Growth

Shows the percentage change in company revenue.

### Profit Growth

Shows the percentage change in company profit.

### Debt-to-Equity Ratio

Indicates the relationship between company debt and equity.

### Current Ratio

Provides an indication of short-term liquidity.

### Net Profit Margin

Shows the percentage of revenue retained as net profit.

These indicators are combined using predefined thresholds to determine the overall risk level.

---

## Risk Classification

The current MVP uses predefined threshold-based rules.

```text
Financial Indicators
        ↓
Threshold Evaluation
        ↓
Risk Assessment
        ↓
LOW / MODERATE / HIGH
```

This approach makes the current risk classification transparent and deterministic.

The project does **not** currently claim to use a trained machine-learning model for the final risk classification.

---

## Responsible AI

FinRisk AI is designed so that the AI component does not become the sole decision-maker.

The system follows these principles:

* Financial calculations are performed before the AI explanation.
* Gemini receives already-calculated values.
* Gemini cannot override the deterministic risk classification.
* AI failures do not block the underlying financial analysis.
* API credentials remain on the backend.
* AI-generated explanations are treated as informational.
* Important financial decisions should receive appropriate human or professional review.

FinRisk AI is a decision-support prototype and is **not a substitute for professional financial, investment, lending, credit, tax, or legal advice**.

---

## Sustainability Context

FinRisk AI connects financial technology with responsible decision-making.

The project focuses on improving awareness of financial health and encouraging more informed evaluation of financial information.

Its sustainability relevance is primarily connected to:

### SDG 12 — Responsible Consumption and Production

The project supports responsible decision-making by making financial information easier to interpret and review.

The current MVP does **not** calculate:

* Carbon emissions
* Energy consumption
* Water usage
* ESG scores
* Environmental impact metrics

These areas may be considered in future versions if reliable sustainability data is incorporated.

---

## Getting Started

### Prerequisites

* Python 3.11+
* Node.js
* npm
* Git

---

## Backend Setup

From the project root:

```bash
python -m venv .venv
```

### Windows

```cmd
.venv\Scripts\activate
```

Install the Python dependencies:

```cmd
pip install -r requirements.txt
```

Create your environment configuration as required by the project.

The Gemini integration uses:

```text
GEMINI_API_KEY
GEMINI_MODEL
AI_TIMEOUT_SECONDS
```

Database and application configuration are handled through the backend configuration system.

---

## Run the Backend

From the project root:

```cmd
.venv\Scripts\python -m uvicorn backend.main:app --reload
```

The FastAPI development server will normally be available at:

```text
http://127.0.0.1:8000
```

---

## Frontend Setup

Open another terminal and navigate to the frontend:

```cmd
cd frontend
```

Install dependencies:

```cmd
npm install
```

Run the development server:

```cmd
npm run dev
```

The Vite development server will display the local frontend address in the terminal.

---

## Production Build

To create a production build:

```cmd
npm run build
```

The production files are generated in:

```text
frontend/dist/
```

---

## Testing

Backend tests are written using pytest.

From the project root:

```cmd
.venv\Scripts\python -m pytest
```

The project was tested during development to verify the risk engine, API behaviour, financial-data handling, and AI integration components.

---

## Deployment

### Frontend

The current frontend is deployed using Netlify:

**Live Application:**
https://finriskai.netlify.app/

### Backend

The FastAPI backend is designed for deployment using Render.

The frontend communicates with the backend through the configured API base URL.

---

## Environment Variables

The project uses environment-based configuration for sensitive or environment-specific values.

Important configuration includes:

```text
DATABASE_URL
APP_ENV
VITE_API_BASE_URL
GEMINI_API_KEY
GEMINI_MODEL
AI_TIMEOUT_SECONDS
```

### Security

The Gemini API key must remain on the backend and should never be placed directly in frontend source code or committed to GitHub.

The project's `.gitignore` should exclude local environment files and other sensitive/generated files.

---

## Current Scope

The current FinRisk AI MVP provides:

* Financial data processing
* Financial indicator calculation
* Rule-based risk classification
* Risk recommendation/explanation logic
* Gemini-powered natural-language explanation
* React dashboard
* FastAPI backend
* SQLite/SQLAlchemy data layer
* Automated testing
* Web deployment

The system is intended as a **working prototype for financial risk analysis and responsible decision support**.

---

## Future Scope

Potential future improvements include:

* Machine-learning-based risk prediction
* Historical financial trend analysis
* Anomaly and early-warning detection
* Sector-specific benchmarking
* Scenario and stress testing
* More financial indicators
* Explainable ML models
* Historical risk tracking
* More advanced sustainability indicators
* Improved financial-data coverage
* Additional AI providers
* Larger-scale deployment and monitoring

These features are **future possibilities and are not represented as current capabilities of the MVP**.

---

## Limitations

FinRisk AI is a prototype and has several limitations:

* Financial analysis depends on the availability and quality of financial data.
* Current risk classification is threshold-based rather than trained from a historical labelled dataset.
* The AI explanation depends on the availability of the Gemini API.
* The application should not be used as the sole basis for consequential financial decisions.
* The current sustainability connection is focused on responsible financial decision-making rather than direct environmental measurement.

---

## Project Context

This project was developed as part of the:

**1M1B AI for Sustainability Virtual Internship**

In collaboration with:

* IBM SkillsBuild
* AICTE

Development assistance was provided using **IBM Bob**, while Google Gemini is integrated into the application itself as the natural-language explanation provider.

---

## Development Philosophy

The project follows a separation between:

```text
Financial Logic
      ↓
Deterministic Result
      ↓
AI Explanation
```

This design helps keep the core financial assessment predictable while using generative AI where it provides the most value: **explaining already-calculated results in an accessible way**.

---

## License

This project was created as an educational and internship prototype.

Please review the repository owner and project terms before reusing the source code for commercial purposes.
