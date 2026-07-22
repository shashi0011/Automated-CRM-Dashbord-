const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Submitted (persisted) interactions — history panel only.
  listInteractions: () => request('/api/interactions'),
  updateInteraction: (id, payload) =>
    request(`/api/interactions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteInteraction: (id) =>
    request(`/api/interactions/${id}`, { method: 'DELETE' }),

  // Draft (the AI-controlled left form) — never written to directly.
  getDraft: (sessionId) => request(`/api/draft/${sessionId}`),
  submitDraft: (sessionId) =>
    request(`/api/draft/${sessionId}/submit`, { method: 'POST' }),
  resetDraft: (sessionId) =>
    request(`/api/draft/${sessionId}`, { method: 'DELETE' }),

  // Chat — the only thing allowed to mutate the draft.
  sendChatMessage: (sessionId, message) =>
    request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message }),
    }),
  resetChatSession: (sessionId) =>
    request(`/api/chat/${sessionId}`, { method: 'DELETE' }),
};
