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
      'Cannot connect to FastAPI. Start the backend on port 8000.'
    )
  }

  const text = await response.text()
  let data

  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { detail: text }
  }

  if (!response.ok) {
    const detail =
      data.detail || data.message || `HTTP ${response.status}`

    throw new Error(
      typeof detail === 'string'
        ? detail
        : JSON.stringify(detail)
    )
  }

  return data
}

function threadPath(threadId) {
  if (!threadId || !threadId.trim()) {
    throw new Error('Workflow thread ID is required.')
  }

  return `/${encodeURIComponent(threadId.trim())}`
}

export const coordinatorApi = {

  // Start default mock workflow or selected project
  start: (projectId = '') =>
    request(
      projectId
        ? `/start?project_id=${encodeURIComponent(projectId)}`
        : '/start',
      {
        method: 'POST',
      }
    ),

  // Create a real project in Neon PostgreSQL
  createProject: (name, description) =>
    request('/projects', {
      method: 'POST',
      body: JSON.stringify({
        name,
        description,
      }),
    }),

  // Retrieve saved projects
  listProjects: () =>
    request('/projects'),

  // Existing Coordinator endpoints
  status: (threadId) =>
    request(`${threadPath(threadId)}/status`),

  review: (threadId, decision, feedback = '') =>
    request(`${threadPath(threadId)}/review`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        feedback,
      }),
    }),

  history: (threadId) =>
    request(`${threadPath(threadId)}/history`),

  report: (threadId) =>
    request(`${threadPath(threadId)}/report`),
}
