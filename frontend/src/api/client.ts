const API_BASE = "http://localhost:8000";

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);

  let body: unknown = null;
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    body = await response.json();
  }

  if (!response.ok) {
    const message =
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof (body as { detail?: unknown }).detail === "string"
        ? (body as { detail: string }).detail
        : `Request failed: ${response.status} ${response.statusText}`;

    throw new Error(message);
  }

  return body as T;
}

export { API_BASE };
