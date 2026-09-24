import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App.jsx";

const board = {
  id: "board-1",
  name: "SparkBoard",
  lanes: [
    { key: "backlog", title: "Backlog", cards: [] },
    { key: "in_progress", title: "In progress", cards: [] },
    { key: "shipped", title: "Shipped", cards: [] },
  ],
};

function json(data, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  };
}

describe("SparkBoard frontend", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url, options = {}) => {
        const method = options.method || "GET";
        if (url.endsWith("/api/boards") && method === "GET") {
          return json([{ id: "board-1", name: "SparkBoard" }]);
        }
        if (url.endsWith("/api/boards/board-1") && method === "GET") {
          return json(board);
        }
        if (url.endsWith("/api/boards/board-1/cards") && method === "POST") {
          const body = JSON.parse(options.body);
          board.lanes[0].cards.push({
            id: "card-1",
            board_id: "board-1",
            lane: "backlog",
            title: body.title,
            description: "",
            position: 0,
          });
          return json(board.lanes[0].cards[0], 201);
        }
        return json({ detail: "not mocked" }, 500);
      })
    );
  });

  afterEach(() => {
    board.lanes.forEach((lane) => {
      lane.cards = [];
    });
    vi.unstubAllGlobals();
  });

  it("renders three lanes from the API", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "SparkBoard" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Backlog" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "In progress" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Shipped" })).toBeInTheDocument();
  });

  it("adds a card through the API contract", async () => {
    const user = userEvent.setup();
    render(<App />);
    const input = await screen.findByLabelText("Add card to Backlog");
    await user.type(input, "Write product spec");
    await user.click(screen.getAllByRole("button", { name: "Add" })[0]);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Write product spec" })).toBeInTheDocument();
    });
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/boards/board-1/cards",
      expect.objectContaining({ method: "POST" })
    );
  });
});
