function getDefaultApiBaseUrl() {
  if (typeof window === "undefined") {
    return "http://localhost:8000/api/v1";
  }
  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  const host = window.location.hostname || "localhost";
  return `${protocol}//${host}:8000/api/v1`;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl();

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

  let response;
  try {
    response = await fetch(buildUrl(path), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error(
      `无法连接后端服务：${API_BASE_URL}。请确认后端已启动，或设置 VITE_API_BASE_URL。`,
    );
  }

  if (!response.ok) {
    let message = `请求失败 (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) {
        message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // 无法解析响应体，使用默认消息
    }
    throw new Error(message);
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

export async function apiDownload(path) {
  const headers = {};
  const token = getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(buildUrl(path), {
      method: "GET",
      headers,
    });
  } catch {
    throw new Error(
      `无法连接后端服务：${API_BASE_URL}。请确认后端已启动，或设置 VITE_API_BASE_URL。`,
    );
  }

  if (!response.ok) {
    let message = `下载失败 (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) {
        message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // ignore parse error
    }
    throw new Error(message);
  }

  return response.blob();
}
