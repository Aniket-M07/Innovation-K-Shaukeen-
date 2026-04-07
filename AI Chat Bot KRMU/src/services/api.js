const getAPIBaseURL = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  const host = window.location.hostname;
  const port = 5000;
  return `http://${host}:${port}/api`;
};

const API_BASE_URL = getAPIBaseURL();
const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 20000);

const getToken = () => localStorage.getItem("sca_token");

const parseResponse = async (response) => {
  const raw = await response.text();
  let body = {};

  try {
    body = raw ? JSON.parse(raw) : {};
  } catch {
    body = { message: raw };
  }

  if (!response.ok) {
    const primary = body?.message || body?.detail || "Request failed";
    const secondary = body?.error || "";
    throw new Error(secondary ? `${primary}: ${secondary}` : primary);
  }

  return body;
};

const request = async (path, options = {}) => {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    return await parseResponse(
      await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
        signal: controller.signal,
      })
    );
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
};

export const loginUser = async (payload) =>
  request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const registerUser = async (payload) =>
  request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const createAdminUser = async (payload) =>
  request("/auth/create-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const sendChatQuery = async (message) =>
  request("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

export const fetchChatHistory = async (limit = 50) =>
  request(`/chat/history?limit=${Math.max(1, Math.min(200, Number(limit) || 50))}`);

export const submitChatFeedback = async (chatId, rating, comment) =>
  request(`/chat/${chatId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating, comment }),
  });

export const fetchAdminAnalytics = async () => request("/admin/analytics");
export const fetchAdminDocuments = async () => request("/admin/documents");

export const uploadAdminDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return request("/admin/upload", {
    method: "POST",
    body: formData,
  });
};

export const deleteAdminDocument = async (id) =>
  request(`/admin/document/${id}`, {
    method: "DELETE",
  });