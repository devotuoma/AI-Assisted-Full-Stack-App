# AI-Assisted-Full-Stack-App
Mini Kanban board






# SparkBoard

Mini Kanban board for DataTalksClub AI Dev Tools Zoomcamp Module 2. Three fixed lanes, FastAPI backend, SQLite persistence, no paid APIs.

## Homework answers (local)

| Question | Answer |
| --- | --- |
| 1. Which project did you choose? | Mini Kanban board |
| 2. What is the name you chose? | SparkBoard |
| 4. Start the frontend | `npm run dev` (from `frontend/`) or `make frontend` |
| 5. Start the backend | `uv run uvicorn app.main:app --reload --port 8000` (from `backend/`) or `make backend` |
| 6. Frontend → backend URL | `http://localhost:8000/api` |
| 7. Run tests | `make test` |

Question 3 (commit SHA1) is filled after you commit. Run `git rev-parse HEAD`.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+

## Run locally

Terminal 1 — backend:

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The UI calls `http://localhost:8000/api`. Data is stored in `backend/sparkboard.db`.

## Tests

```bash
make test
```

Equivalent commands:

```bash
cd backend && uv sync --extra dev && uv run pytest ../tests
cd frontend && npm test
```

## Layout

```
product-spec.md
AGENTS.md
openapi.yaml
frontend/
backend/
tests/
docs/ai-usage-report.md
```
