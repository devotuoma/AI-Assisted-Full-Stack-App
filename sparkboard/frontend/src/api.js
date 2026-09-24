export const API_BASE_URL = "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) {
    return null;
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return body;
}

export const api = {
  listBoards: () => request("/boards"),
  getBoard: (id) => request(`/boards/${id}`),
  createBoard: (name) => request("/boards", { method: "POST", body: JSON.stringify({ name }) }),
  deleteBoard: (id) => request(`/boards/${id}`, { method: "DELETE" }),
  createCard: (boardId, payload) =>
    request(`/boards/${boardId}/cards`, { method: "POST", body: JSON.stringify(payload) }),
  updateCard: (cardId, payload) =>
    request(`/cards/${cardId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteCard: (cardId) => request(`/cards/${cardId}`, { method: "DELETE" }),
};
