const API_BASE_URL = "http://127.0.0.1:8000";

export async function analyzeRequirements(payload) {
  const response = await fetch(
    `${API_BASE_URL}/requirements/analyze`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Request failed with status ${response.status}: ${errorText}`
    );
  }

  return response.json();
}