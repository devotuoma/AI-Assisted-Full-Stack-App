# Agent notes for SparkBoard

## Source of truth

1. `product-spec.md` — behavior and non-goals
2. `openapi.yaml` — HTTP contract; do not invent endpoints the frontend does not use
3. This file — how to change the repo

## Layout

- `frontend/` Vite + React (JavaScript)
- `backend/` FastAPI app package `app`
- `tests/` pytest against the FastAPI app
- `docs/ai-usage-report.md` — what AI generated vs what was verified

## Rules

- Keep the board store behind `app.store.BoardStore`. Do not query SQL from route handlers.
- Default lanes are fixed: `backlog`, `in_progress`, `shipped`. Do not add custom columns.
- Reject empty titles. Do not delete the last board.
- CORS must allow `http://localhost:5173`.
- No paid APIs, no secrets in git, no Docker in Module 2 unless the human asks.

## Commands

See `README.md`. Prefer `make backend`, `make frontend`, and `make test`.
