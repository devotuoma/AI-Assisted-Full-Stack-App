import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import "./App.css";

const LANE_FLOW = ["backlog", "in_progress", "shipped"];

function neighbor(lane, direction) {
  const index = LANE_FLOW.indexOf(lane);
  return LANE_FLOW[index + direction] || null;
}

export default function App() {
  const [boards, setBoards] = useState([]);
  const [board, setBoard] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [newBoardName, setNewBoardName] = useState("");
  const [drafts, setDrafts] = useState({});
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);

  async function loadBoards(preferredId) {
    const list = await api.listBoards();
    setBoards(list);
    const nextId = preferredId || selectedId || list[0]?.id;
    if (!nextId) {
      setBoard(null);
      return;
    }
    setSelectedId(nextId);
    setBoard(await api.getBoard(nextId));
  }

  useEffect(() => {
    loadBoards().catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const title = useMemo(() => board?.name || "SparkBoard", [board]);

  async function wrap(action) {
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err.message);
    }
  }

  function onCreateBoard(event) {
    event.preventDefault();
    wrap(async () => {
      const created = await api.createBoard(newBoardName);
      setNewBoardName("");
      await loadBoards(created.id);
    });
  }

  function onCreateCard(event, lane) {
    event.preventDefault();
    const titleText = (drafts[lane] || "").trim();
    wrap(async () => {
      await api.createCard(board.id, { title: titleText, description: "", lane });
      setDrafts((current) => ({ ...current, [lane]: "" }));
      setBoard(await api.getBoard(board.id));
    });
  }

  function onMove(card, direction) {
    const lane = neighbor(card.lane, direction);
    if (!lane) return;
    wrap(async () => {
      await api.updateCard(card.id, { lane });
      setBoard(await api.getBoard(board.id));
    });
  }

  function onSaveEdit(event) {
    event.preventDefault();
    wrap(async () => {
      await api.updateCard(editing.id, {
        title: editing.title,
        description: editing.description,
      });
      setEditing(null);
      setBoard(await api.getBoard(board.id));
    });
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Mini Kanban</p>
          <h1>{title}</h1>
          <p className="lede">Three lanes. SQLite persistence. No paid APIs.</p>
        </div>
        <form className="board-switch" onSubmit={onCreateBoard}>
          <label>
            Board
            <select
              value={selectedId}
              onChange={(event) => wrap(() => loadBoards(event.target.value))}
            >
              {boards.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <input
            value={newBoardName}
            onChange={(event) => setNewBoardName(event.target.value)}
            placeholder="New board name"
            aria-label="New board name"
          />
          <button type="submit">Create board</button>
          <button
            type="button"
            className="danger"
            onClick={() =>
              wrap(async () => {
                await api.deleteBoard(selectedId);
                setSelectedId("");
                await loadBoards();
              })
            }
          >
            Delete board
          </button>
        </form>
      </header>

      {error ? <p className="banner" role="alert">{error}</p> : null}

      <section className="board" aria-label="Kanban board">
        {(board?.lanes || []).map((lane) => (
          <article key={lane.key} className="lane" data-lane={lane.key}>
            <header>
              <h2>{lane.title}</h2>
              <span>{lane.cards.length}</span>
            </header>
            <form onSubmit={(event) => onCreateCard(event, lane.key)}>
              <input
                value={drafts[lane.key] || ""}
                onChange={(event) =>
                  setDrafts((current) => ({ ...current, [lane.key]: event.target.value }))
                }
                placeholder="Add a card"
                aria-label={`Add card to ${lane.title}`}
              />
              <button type="submit">Add</button>
            </form>
            <ul>
              {lane.cards.map((card) => (
                <li key={card.id} className="card">
                  {editing?.id === card.id ? (
                    <form className="edit" onSubmit={onSaveEdit}>
                      <input
                        value={editing.title}
                        onChange={(event) => setEditing({ ...editing, title: event.target.value })}
                        aria-label="Edit title"
                      />
                      <textarea
                        value={editing.description}
                        onChange={(event) =>
                          setEditing({ ...editing, description: event.target.value })
                        }
                        aria-label="Edit description"
                      />
                      <div className="row">
                        <button type="submit">Save</button>
                        <button type="button" onClick={() => setEditing(null)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <h3>{card.title}</h3>
                      {card.description ? <p>{card.description}</p> : null}
                      <div className="row">
                        <button
                          type="button"
                          disabled={!neighbor(card.lane, -1)}
                          onClick={() => onMove(card, -1)}
                        >
                          ←
                        </button>
                        <button
                          type="button"
                          disabled={!neighbor(card.lane, 1)}
                          onClick={() => onMove(card, 1)}
                        >
                          →
                        </button>
                        <button type="button" onClick={() => setEditing(card)}>
                          Edit
                        </button>
                        <button
                          type="button"
                          className="danger"
                          onClick={() =>
                            wrap(async () => {
                              await api.deleteCard(card.id);
                              setBoard(await api.getBoard(board.id));
                            })
                          }
                        >
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </main>
  );
}
