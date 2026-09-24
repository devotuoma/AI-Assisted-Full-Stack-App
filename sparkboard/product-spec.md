# SparkBoard — Product Spec

SparkBoard is a mini Kanban board for a single operator tracking work across three fixed lanes. It is the Module 2 homework app: a maintainable frontend, an OpenAPI contract, a FastAPI backend, and SQLite persistence. No paid APIs or model credits.

## Problem

People dump tasks into notes and lose the “what is in flight?” view. SparkBoard gives one named board with three lanes so a refresh still shows the same cards.

## User stories and acceptance criteria

### US-1 — Open a board

**As a** user, **I want** a board with three lanes **so that** I can see work at a glance.

- Given the app is running, when I open the frontend, I see a board named “SparkBoard” (created if missing).
- The lanes are **Backlog**, **In progress**, and **Shipped**, in that order.
- Empty lanes still render and show a count of `0`.

### US-2 — Add a card

**As a** user, **I want** to add a card to a lane **so that** I can capture a task.

- Given I type a non-empty title in a lane, when I submit, the card appears at the bottom of that lane.
- Title is required (1–120 characters). Description is optional (max 2000 characters).
- The backend returns `400` when the title is blank or whitespace-only.
- After a full page reload, the card is still there.

### US-3 — Move a card

**As a** user, **I want** to move a card to another lane **so that** I can update status.

- Each card has controls to move left and right (when a neighbor lane exists).
- Moving a card appends it to the destination lane.
- Persistence matches the last successful move after reload.

### US-4 — Edit and delete a card

**As a** user, **I want** to edit or delete a card **so that** the board stays accurate.

- I can change title and description; an empty title is rejected.
- Delete removes the card from the board and from the database.
- Deleting an unknown card id returns `404`.

### US-5 — Multiple boards

**As a** user, **I want** more than one board **so that** I can separate projects.

- I can create a board with a name (1–80 characters).
- I can switch boards in the UI.
- Deleting a board deletes its cards. The last remaining board cannot be deleted (`409`).

## Non-goals

- Accounts, login, SSO, or multi-user realtime sync
- Custom lane names, WIP limits, labels, assignees, due dates, attachments
- Drag-and-drop libraries, notifications, or email
- Hosted LLM calls or any paid third-party API
- Production deployment, CI/CD, and containers (Module 3)

## Technical constraints

- Frontend talks to the backend using the OpenAPI contract in `openapi.yaml`
- Backend is FastAPI; storage is behind a store interface (memory for tests, SQLite for local run)
- SQLite file: `backend/sparkboard.db` (gitignored)
- Frontend origin: `http://localhost:5173`
- Backend origin: `http://localhost:8000`
- API base URL used by the frontend: `http://localhost:8000/api`
- Postgres can replace SQLite later by swapping the store implementation only
