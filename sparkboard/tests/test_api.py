from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app
from app.store import MemoryStore, SqliteStore


@pytest.fixture
def memory_client() -> TestClient:
    return TestClient(create_app(MemoryStore()))


@pytest.fixture
def sqlite_client(tmp_path: Path) -> TestClient:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    return TestClient(create_app(SqliteStore(url)))


@pytest.mark.parametrize("client_name", ["memory_client", "sqlite_client"])
def test_health(client_name: str, request: pytest.FixtureRequest) -> None:
    client: TestClient = request.getfixturevalue(client_name)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("client_name", ["memory_client", "sqlite_client"])
def test_default_board_has_three_lanes(client_name: str, request: pytest.FixtureRequest) -> None:
    client: TestClient = request.getfixturevalue(client_name)
    boards = client.get("/api/boards").json()
    assert len(boards) == 1
    assert boards[0]["name"] == "SparkBoard"
    detail = client.get(f"/api/boards/{boards[0]['id']}").json()
    assert [lane["key"] for lane in detail["lanes"]] == ["backlog", "in_progress", "shipped"]
    assert all(lane["cards"] == [] for lane in detail["lanes"])


@pytest.mark.parametrize("client_name", ["memory_client", "sqlite_client"])
def test_create_move_edit_delete_card(client_name: str, request: pytest.FixtureRequest) -> None:
    client: TestClient = request.getfixturevalue(client_name)
    board_id = client.get("/api/boards").json()[0]["id"]

    created = client.post(
        f"/api/boards/{board_id}/cards",
        json={"title": "Write OpenAPI", "description": "contract first", "lane": "backlog"},
    )
    assert created.status_code == 201
    card = created.json()
    assert card["lane"] == "backlog"
    assert card["position"] == 0

    blank = client.post(
        f"/api/boards/{board_id}/cards",
        json={"title": "   ", "lane": "backlog"},
    )
    assert blank.status_code == 400

    moved = client.patch(f"/api/cards/{card['id']}", json={"lane": "in_progress"})
    assert moved.status_code == 200
    assert moved.json()["lane"] == "in_progress"

    edited = client.patch(f"/api/cards/{card['id']}", json={"title": "Ship OpenAPI"})
    assert edited.json()["title"] == "Ship OpenAPI"

    board = client.get(f"/api/boards/{board_id}").json()
    by_lane = {lane["key"]: lane["cards"] for lane in board["lanes"]}
    assert by_lane["backlog"] == []
    assert by_lane["in_progress"][0]["title"] == "Ship OpenAPI"

    deleted = client.delete(f"/api/cards/{card['id']}")
    assert deleted.status_code == 204
    missing = client.delete(f"/api/cards/{card['id']}")
    assert missing.status_code == 404


@pytest.mark.parametrize("client_name", ["memory_client", "sqlite_client"])
def test_cannot_delete_last_board(client_name: str, request: pytest.FixtureRequest) -> None:
    client: TestClient = request.getfixturevalue(client_name)
    board_id = client.get("/api/boards").json()[0]["id"]
    blocked = client.delete(f"/api/boards/{board_id}")
    assert blocked.status_code == 409

    extra = client.post("/api/boards", json={"name": "Side project"})
    assert extra.status_code == 201
    deleted = client.delete(f"/api/boards/{board_id}")
    assert deleted.status_code == 204
    leftover = client.get("/api/boards").json()
    assert len(leftover) == 1
    assert leftover[0]["name"] == "Side project"
