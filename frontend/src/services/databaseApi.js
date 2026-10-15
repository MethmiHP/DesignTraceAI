const API_BASE = "/api/database-design";

export async function generateDatabaseDesign(payload) {
  const response = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      `The server returned an unreadable response (HTTP ${response.status}).`
    );
  }

  if (!response.ok) {
    const detail = data?.detail;

    if (typeof detail === "string") {
      throw new Error(detail);
    }

    if (Array.isArray(detail)) {
      throw new Error(
        detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
      );
    }

    throw new Error(
      `Database generation failed (HTTP ${response.status}).`
    );
  }

  return data;
}

export function downloadFile(filename, content, mimeType = "text/plain") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
