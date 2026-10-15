const TRACEABILITY_API_URL =
  'http://127.0.0.1:8000/traceability/analyze'

export async function analyzeTraceability(payload) {
  const response = await fetch(
    TRACEABILITY_API_URL,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    let message = 'Traceability analysis failed.'

    try {
      const errorData = await response.json()

      if (errorData.detail) {
        message = errorData.detail
      }
    } catch {
      // Keep default message.
    }

    throw new Error(message)
  }

  return await response.json()
}