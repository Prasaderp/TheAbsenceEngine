import type { ApiError } from "@/types";

class ApiClientError extends Error {
  code: string;
  requestId: string;
  status: number;
  constructor(message: string, code: string, requestId: string, status: number) {
    super(message);
    this.code = code;
    this.requestId = requestId;
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (init.body instanceof FormData) delete headers["Content-Type"];

  const res = await fetch(`/api/v1${path}`, { ...init, headers });

  if (!res.ok) {
    if (res.status === 401 && path !== "/auth/login" && path !== "/auth/refresh") {
      await tryRefresh();
      return request<T>(path, init);
    }
    const body = (await res.json().catch(() => ({ error: { code: "UNKNOWN", message: res.statusText, request_id: "" } }))) as ApiError;
    throw new ApiClientError(body.error.message, body.error.code, body.error.request_id, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function tryRefresh(): Promise<void> {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) { clearTokens(); return; }
  try {
    const res = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) { clearTokens(); return; }
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
  } catch { clearTokens(); }
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export { ApiClientError };
