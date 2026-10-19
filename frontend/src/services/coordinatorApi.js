const BASE = '/api/coordinator'

async function request(path, options = {}) {
  let response

  try {
    response = await fetch(`${BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch {
    throw new Error(
      'Cannot connect to the backend. Start FastAPI on port 8000.'
    )
  }

  const raw = await response.text()
  let data

  try {
    data = raw ? JSON.parse(raw) : {}
  } catch {
    data = { detail: raw }
  }

  if (!response.ok) {
    const detail = data.detail || data.message || `HTTP ${response.status}`
    throw new Error(
      typeof detail === 'string' ? detail : JSON.stringify(detail)
    )
  }

  return data
}

// These paths assume your four Swagger operations use:
// POST /start
// GET  /{thread_id}/status
// POST /{thread_id}/review
// GET  /{thread_id}/report
//
// Compare them with http://127.0.0.1:8000/docs.
// If your actual paths or request schemas differ,
// adjust this file only.

export const coordinatorApi = {
  start: (payload) =>
    request('/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  status: (threadId) =>
    request(`/${encodeURIComponent(threadId)}/status`),

  review: (threadId, decision, feedback = '') =>
    request(`/${encodeURIComponent(threadId)}/review`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        feedback,
      }),
    }),

  report: (threadId) =>
    request(`/${encodeURIComponent(threadId)}/report`),
}