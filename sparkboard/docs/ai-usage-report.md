# AI usage report — SparkBoard (Module 2)

Tool: Cursor (Grok 4.6). No Lovable/Bolt prototype, no paid model APIs inside the app.

## Workflow (controlled, not one-shot)

1. Wrote `product-spec.md` before application code: user stories, acceptance criteria, non-goals, constraints.
2. Drafted `openapi.yaml` as the frontend/backend contract.
3. Generated a Vite React frontend that only calls paths from that contract (`/api/boards`, `/api/cards`).
4. Implemented FastAPI against the contract with a `BoardStore` protocol, `MemoryStore` for tests, `SqliteStore` for local runs.
5. Added pytest coverage for health, default board, card CRUD/move, last-board delete rule — on both stores.
6. Added Vitest + Testing Library checks for lane rendering and card creation against `http://localhost:8000/api`.

## What was verified by a human-in-the-loop agent run

- Backend tests against memory and SQLite
- Frontend unit tests with a mocked `fetch`
- Commands in `README.md` match the homework questions

## What AI was not allowed to do

- Invent extra endpoints (auth, websockets, custom lanes)
- Add Docker/CI (Module 3)
- Call hosted LLMs from the product
