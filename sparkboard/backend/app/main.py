from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.store import BoardStore, SqliteStore, StoreError

DB_PATH = Path(__file__).resolve().parent.parent / "sparkboard.db"


class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    lane: str

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        return value.strip()


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    lane: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


def create_app(board_store: BoardStore | None = None) -> FastAPI:
    store = board_store or SqliteStore(os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}"))
    store.ensure_default_board()

    app = FastAPI(title="SparkBoard API", version="1.0.0")
    app.state.store = store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StoreError)
    def handle_store_error(_request: Request, exc: StoreError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    def handle_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        loc = first.get("loc", ["body"])[-1]
        return JSONResponse(status_code=400, content={"detail": f"invalid {loc}"})

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/boards")
    def list_boards() -> list[dict]:
        return store.list_boards()

    @app.post("/api/boards", status_code=201)
    def create_board(body: BoardCreate) -> dict:
        return store.create_board(body.name)

    @app.get("/api/boards/{board_id}")
    def get_board(board_id: str) -> dict:
        return store.get_board(board_id)

    @app.delete("/api/boards/{board_id}", status_code=204)
    def delete_board(board_id: str) -> None:
        store.delete_board(board_id)

    @app.post("/api/boards/{board_id}/cards", status_code=201)
    def create_card(board_id: str, body: CardCreate) -> dict:
        return store.create_card(board_id, body.title, body.description, body.lane)

    @app.patch("/api/cards/{card_id}")
    def update_card(card_id: str, body: CardUpdate) -> dict:
        return store.update_card(card_id, body.model_dump(exclude_unset=True))

    @app.delete("/api/cards/{card_id}", status_code=204)
    def delete_card(card_id: str) -> None:
        store.delete_card(card_id)

    return app


app = create_app()
