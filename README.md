# Agentic Commerce MVP

An AI-native commerce platform enabling merchants to expose their catalog and commerce capabilities once, then sell through both an in-app shopping agent on the merchant storefront and external AI buyers connected via MCP.

The common commerce service layer and backend SQLite database act as the authoritative source of truth for all products, inventory, prices, carts, quotes, merchant policies, and orders.

---

## Architecture

- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS v4
- **Backend**: FastAPI + Python 3.12+ + SQLAlchemy 2.x + Alembic
- **Database**: Local SQLite (`backend/data/store.db`)
- **Payments**: Razorpay Test Mode with explicit approval step

---

## Local Setup

### Prerequisites
- Python 3.12+ (Python 3.13 supported)
- Node.js 20+ and npm
- `uv` (recommended) or standard `pip`

### 1. Environment Setup

Copy `.env.example` to `.env` in the root (or set per backend/frontend):
```bash
cp .env.example .env
```

### Quick Start (One Command on Windows)

From the project root:
```powershell
.\run-local.ps1
```
This opens both the FastAPI backend and Vite frontend in dedicated terminal windows.

---

### Manual Setup (Step-by-Step)

### 2. Backend Setup & Database Seed

```bash
cd backend

# Create virtual environment and install dependencies
uv venv
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate
uv pip install -e .

# Run database migrations
alembic upgrade head

# Seed merchant, demo admin, realistic catalog & policies (one command)
python -m app.db.seed

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

The backend will run at `http://localhost:8000`.
- Health Check: `http://localhost:8000/api/health`
- Products API: `http://localhost:8000/api/products`
- Interactive Docs: `http://localhost:8000/docs`

### 3. Frontend Setup

In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173`.

---

## Project Structure

```text
├── context/               # PRD, Architecture, Build Plan, Design Tokens, API specs
├── backend/               # FastAPI backend
│   ├── alembic/           # Alembic database migrations
│   ├── app/
│   │   ├── api/routes/    # API routes (health, products, etc.)
│   │   ├── core/          # Config & CORS setup
│   │   ├── db/            # Database session, base & seed scripts
│   │   ├── models/        # SQLAlchemy models (authoritative entities)
│   │   └── schemas/       # Pydantic request/response schemas
│   └── data/              # Local SQLite database storage
└── frontend/              # React + Vite + TypeScript
    └── src/
        ├── lib/api/       # Typed API client
        ├── styles/        # Global CSS & Tailwind v4 theme tokens
        └── types/         # Domain TypeScript types
```
