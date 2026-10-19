const API_BASE_URL = 'http://127.0.0.1:8000/api/adr'

async function handleResponse(response) {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`

    try {
      const data = await response.json()
      message = data.detail || message
    } catch {
      // Keep default message.
    }

    throw new Error(message)
  }

  return response.json()
}

export async function getProjectADRs(projectId) {
  const response = await fetch(
    `${API_BASE_URL}/project/${encodeURIComponent(projectId)}`
  )

  return handleResponse(response)
}

export async function getADRById(adrId) {
  const response = await fetch(
    `${API_BASE_URL}/${encodeURIComponent(adrId)}`
  )

  return handleResponse(response)
}

export async function updateADRStatus(adrId, status) {
  const response = await fetch(
    `${API_BASE_URL}/${encodeURIComponent(adrId)}/status/${encodeURIComponent(status)}`,
    {
      method: 'PATCH',
    }
  )

  return handleResponse(response)
}

export async function supersedeADR(oldAdrId, newAdrId) {
  const response = await fetch(
    `${API_BASE_URL}/${encodeURIComponent(oldAdrId)}/supersede/${encodeURIComponent(newAdrId)}`,
    {
      method: 'POST',
    }
  )

  return handleResponse(response)
}

export async function generateADRs(payload) {
  const response = await fetch(
    `${API_BASE_URL}/generate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )

  return handleResponse(response)
}