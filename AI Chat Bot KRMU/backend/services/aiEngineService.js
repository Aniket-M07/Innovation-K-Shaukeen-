import fs from "fs/promises";

const AI_ENGINE_BASE_URL = process.env.AI_ENGINE_BASE_URL || "http://127.0.0.1:8000";
const AI_ENGINE_TIMEOUT_MS = Number(process.env.AI_ENGINE_TIMEOUT_MS || 30000);

const clampTopK = (value) => Math.max(1, Math.min(10, Number(value) || 4));

const fetchWithTimeout = async (url, options = {}, timeoutMs = AI_ENGINE_TIMEOUT_MS) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    const raw = await response.text();
    let data;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = { message: raw };
    }

    if (!response.ok) {
      const reason = data?.detail || data?.message || "AI engine request failed";
      throw new Error(reason);
    }

    return data;
  } finally {
    clearTimeout(timeout);
  }
};

export const queryAIEngine = async (query, topK = 4) => {
  return fetchWithTimeout(`${AI_ENGINE_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: clampTopK(topK) }),
  });
};

export const queryAIEngineWithContext = async (query, topK = 4, { feedbackContext = "" } = {}) => {
  return fetchWithTimeout(`${AI_ENGINE_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: clampTopK(topK), feedback_context: feedbackContext }),
  });
};

export const embedFileWithAIEngine = async (file) => {
  const fileBuffer = await fs.readFile(file.path);
  const formData = new FormData();
  const blob = new Blob([fileBuffer], { type: file.mimetype || "application/octet-stream" });

  formData.append("files", blob, file.originalname || file.filename);

  return fetchWithTimeout(`${AI_ENGINE_BASE_URL}/embed`, {
    method: "POST",
    body: formData,
  });
};