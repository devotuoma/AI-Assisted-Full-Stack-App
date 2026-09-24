.PHONY: backend frontend test

backend:
	cd backend && uv sync --extra dev && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm install && npm run dev

test:
	cd backend && uv sync --extra dev && uv run pytest ../tests
	cd frontend && npm install && npm test
