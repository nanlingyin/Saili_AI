const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;

function buildUrl(path) {
  const base = API_BASE_URL.replace(/\/$/, "");
  const endpoint = path.replace(/^\//, "");
  return `${base}/${endpoint}`;
}

export async function apiGet(path) {
  return apiRequest(path, { method: "GET" });
}

function getAuthToken() {
  return localStorage.getItem("auth_token");
}

export async function apiRequest(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body) {
    headers["Content-Type"] = "application/json";
  }
  const token = getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json();
}

export function apiPost(path, payload) {
  return apiRequest(path, { method: "POST", body: payload });
}

export function apiPut(path, payload) {
  return apiRequest(path, { method: "PUT", body: payload });
}

export function apiDelete(path) {
  return apiRequest(path, { method: "DELETE" });
}
