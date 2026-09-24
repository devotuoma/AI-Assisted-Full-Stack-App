from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

LANE_ORDER = ("backlog", "in_progress", "shipped")
LANE_TITLES = {
    "backlog": "Backlog",
    "in_progress": "In progress",
    "shipped": "Shipped",
}


class StoreError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_title(value: str | None, *, field: str, max_len: int) -> str:
    if value is None:
        raise StoreError(400, f"{field} is required")
    title = value.strip()
    if not title:
        raise StoreError(400, f"{field} must not be empty")
    if len(title) > max_len:
        raise StoreError(400, f"{field} is too long")
    return title


def clean_description(value: str | None) -> str:
    text = "" if value is None else value
    if len(text) > 2000:
        raise StoreError(400, "description is too long")
    return text


def require_lane(lane: str) -> str:
    if lane not in LANE_ORDER:
        raise StoreError(400, "lane must be backlog, in_progress, or shipped")
    return lane


class BoardStore(Protocol):
    def ensure_default_board(self) -> dict: ...
    def list_boards(self) -> list[dict]: ...
    def create_board(self, name: str) -> dict: ...
    def get_board(self, board_id: str) -> dict: ...
    def delete_board(self, board_id: str) -> None: ...
    def create_card(self, board_id: str, title: str, description: str, lane: str) -> dict: ...
    def update_card(self, card_id: str, patch: dict) -> dict: ...
    def delete_card(self, card_id: str) -> None: ...


def empty_lanes() -> dict[str, list[dict]]:
    return {key: [] for key in LANE_ORDER}


def assemble_board(board_id: str, name: str, cards_by_lane: dict[str, list[dict]]) -> dict:
    return {
        "id": board_id,
        "name": name,
        "lanes": [
            {
                "key": key,
                "title": LANE_TITLES[key],
                "cards": sorted(cards_by_lane.get(key, []), key=lambda c: c["position"]),
            }
            for key in LANE_ORDER
        ],
    }


class MemoryStore:
    def __init__(self) -> None:
        self._boards: dict[str, dict] = {}
        self._cards: dict[str, dict] = {}

    def ensure_default_board(self) -> dict:
        if not self._boards:
            return self.create_board("SparkBoard")
        return self.get_board(next(iter(self._boards)))

    def list_boards(self) -> list[dict]:
        return [{"id": b["id"], "name": b["name"]} for b in self._boards.values()]

    def create_board(self, name: str) -> dict:
        board_id = str(uuid4())
        self._boards[board_id] = {"id": board_id, "name": clean_title(name, field="name", max_len=80)}
        return self.get_board(board_id)

    def get_board(self, board_id: str) -> dict:
        board = self._boards.get(board_id)
        if not board:
            raise StoreError(404, "board not found")
        grouped = empty_lanes()
        for card in self._cards.values():
            if card["board_id"] == board_id:
                grouped[card["lane"]].append(card)
        return assemble_board(board["id"], board["name"], grouped)

    def delete_board(self, board_id: str) -> None:
        if board_id not in self._boards:
            raise StoreError(404, "board not found")
        if len(self._boards) <= 1:
            raise StoreError(409, "cannot delete the last board")
        del self._boards[board_id]
        self._cards = {cid: c for cid, c in self._cards.items() if c["board_id"] != board_id}

    def create_card(self, board_id: str, title: str, description: str, lane: str) -> dict:
        if board_id not in self._boards:
            raise StoreError(404, "board not found")
        lane = require_lane(lane)
        position = sum(1 for c in self._cards.values() if c["board_id"] == board_id and c["lane"] == lane)
        card = {
            "id": str(uuid4()),
            "board_id": board_id,
            "lane": lane,
            "title": clean_title(title, field="title", max_len=120),
            "description": clean_description(description),
            "position": position,
        }
        self._cards[card["id"]] = card
        return card

    def update_card(self, card_id: str, patch: dict) -> dict:
        card = self._cards.get(card_id)
        if not card:
            raise StoreError(404, "card not found")
        if "title" in patch and patch["title"] is not None:
            card["title"] = clean_title(patch["title"], field="title", max_len=120)
        if "description" in patch and patch["description"] is not None:
            card["description"] = clean_description(patch["description"])
        if "lane" in patch and patch["lane"] is not None:
            new_lane = require_lane(patch["lane"])
            if new_lane != card["lane"]:
                self._repack(card["board_id"], card["lane"], exclude=card_id)
                card["lane"] = new_lane
                card["position"] = sum(
                    1
                    for c in self._cards.values()
                    if c["board_id"] == card["board_id"] and c["lane"] == new_lane and c["id"] != card_id
                )
        return card

    def delete_card(self, card_id: str) -> None:
        card = self._cards.pop(card_id, None)
        if not card:
            raise StoreError(404, "card not found")
        self._repack(card["board_id"], card["lane"])

    def _repack(self, board_id: str, lane: str, exclude: str | None = None) -> None:
        remaining = [
            c
            for c in self._cards.values()
            if c["board_id"] == board_id and c["lane"] == lane and c["id"] != exclude
        ]
        remaining.sort(key=lambda c: c["position"])
        for index, card in enumerate(remaining):
            card["position"] = index


class Base(DeclarativeBase):
    pass


class BoardRow(Base):
    __tablename__ = "boards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), default=utcnow)
    cards: Mapped[list[CardRow]] = relationship(back_populates="board", cascade="all, delete-orphan")


class CardRow(Base):
    __tablename__ = "cards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    board_id: Mapped[str] = mapped_column(String(36), ForeignKey("boards.id"), nullable=False)
    lane: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    board: Mapped[BoardRow] = relationship(back_populates="cards")


def card_to_dict(row: CardRow) -> dict:
    return {
        "id": row.id,
        "board_id": row.board_id,
        "lane": row.lane,
        "title": row.title,
        "description": row.description,
        "position": row.position,
    }


class SqliteStore:
    def __init__(self, url: str = "sqlite:///sparkboard.db") -> None:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self._engine = create_engine(url, connect_args=connect_args)
        Base.metadata.create_all(self._engine)
        self._session = sessionmaker(bind=self._engine, expire_on_commit=False)

    def ensure_default_board(self) -> dict:
        with self._session() as session:
            first = session.scalar(select(BoardRow))
            if first:
                return self.get_board(first.id)
        return self.create_board("SparkBoard")

    def list_boards(self) -> list[dict]:
        with self._session() as session:
            rows = session.scalars(select(BoardRow)).all()
            return [{"id": row.id, "name": row.name} for row in rows]

    def create_board(self, name: str) -> dict:
        board = BoardRow(id=str(uuid4()), name=clean_title(name, field="name", max_len=80), created_at=utcnow())
        with self._session() as session:
            session.add(board)
            session.commit()
            board_id = board.id
        return self.get_board(board_id)

    def get_board(self, board_id: str) -> dict:
        with self._session() as session:
            board = session.get(BoardRow, board_id)
            if not board:
                raise StoreError(404, "board not found")
            grouped = empty_lanes()
            for card in board.cards:
                grouped[card.lane].append(card_to_dict(card))
            return assemble_board(board.id, board.name, grouped)

    def delete_board(self, board_id: str) -> None:
        with self._session() as session:
            count = len(session.scalars(select(BoardRow)).all())
            board = session.get(BoardRow, board_id)
            if not board:
                raise StoreError(404, "board not found")
            if count <= 1:
                raise StoreError(409, "cannot delete the last board")
            session.delete(board)
            session.commit()

    def create_card(self, board_id: str, title: str, description: str, lane: str) -> dict:
        lane = require_lane(lane)
        with self._session() as session:
            board = session.get(BoardRow, board_id)
            if not board:
                raise StoreError(404, "board not found")
            position = sum(1 for c in board.cards if c.lane == lane)
            card = CardRow(
                id=str(uuid4()),
                board_id=board_id,
                lane=lane,
                title=clean_title(title, field="title", max_len=120),
                description=clean_description(description),
                position=position,
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            return card_to_dict(card)

    def update_card(self, card_id: str, patch: dict) -> dict:
        with self._session() as session:
            card = session.get(CardRow, card_id)
            if not card:
                raise StoreError(404, "card not found")
            if "title" in patch and patch["title"] is not None:
                card.title = clean_title(patch["title"], field="title", max_len=120)
            if "description" in patch and patch["description"] is not None:
                card.description = clean_description(patch["description"])
            if "lane" in patch and patch["lane"] is not None:
                new_lane = require_lane(patch["lane"])
                if new_lane != card.lane:
                    old_lane = card.lane
                    board_id = card.board_id
                    card.lane = new_lane
                    siblings = [
                        c
                        for c in session.scalars(select(CardRow).where(CardRow.board_id == board_id)).all()
                        if c.lane == new_lane and c.id != card.id
                    ]
                    card.position = len(siblings)
                    self._repack_session(session, board_id, old_lane)
            session.commit()
            session.refresh(card)
            return card_to_dict(card)

    def delete_card(self, card_id: str) -> None:
        with self._session() as session:
            card = session.get(CardRow, card_id)
            if not card:
                raise StoreError(404, "card not found")
            board_id, lane = card.board_id, card.lane
            session.delete(card)
            session.flush()
            self._repack_session(session, board_id, lane)
            session.commit()

    def _repack_session(self, session, board_id: str, lane: str) -> None:
        remaining = [
            c
            for c in session.scalars(select(CardRow).where(CardRow.board_id == board_id)).all()
            if c.lane == lane
        ]
        remaining.sort(key=lambda c: c.position)
        for index, card in enumerate(remaining):
            card.position = index
