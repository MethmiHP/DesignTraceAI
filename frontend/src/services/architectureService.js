const API_BASE_URL = "http://127.0.0.1:8000";

export async function analyzeArchitecture(payload, topK = 5) {
  const response = await fetch(
    `${API_BASE_URL}/api/architecture/analyze?top_k=${topK}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        errorData?.detail ||
        "Architecture analysis failed."
    );
  }

  return response.json();
}