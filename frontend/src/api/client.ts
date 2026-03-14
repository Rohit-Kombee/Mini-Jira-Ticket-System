// In dev (npm run dev): use Vite proxy "/api" → http://localhost:8000 (same-origin, no CORS).
// In production: use explicit backend URL (e.g. http://localhost:8000 when served from Docker).
const API_BASE =
  import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== ""
    ? import.meta.env.VITE_API_URL
    : import.meta.env.DEV
      ? "/api"
      : "http://localhost:8000";

function getToken(): string | null {
  return localStorage.getItem("token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  const token = getToken();
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (networkErr) {
    const msg =
      import.meta.env.DEV
        ? "Cannot reach the API. Is the backend running? Start it with: docker compose up backend postgres (or run uvicorn in the backend folder)."
        : "Cannot reach the server. Check that the API is running at " + (API_BASE || "the configured URL") + ".";
    throw new Error(msg);
  }
  if (res.status === 401) {
    localStorage.removeItem("token");
    window.dispatchEvent(new Event("auth:logout"));
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(Array.isArray(err.detail) ? err.detail.map((e: { msg: string }) => e.msg).join(", ") : err.detail || res.statusText);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json();
}
