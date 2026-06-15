/**
 * API Configuration
 * This file is the single source for the core backend used by the frontend.
 * Backend: http://localhost:8000 (or VITE_API_BASE_URL).
 * Start core backend: cd core/backend && uvicorn response:app --reload --port 8000
 */

export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  endpoints: {
    chat: "/chat",
    welcome: "/welcome",
  },
} as const;

export interface HistoryTurn {
  role: "user" | "assistant";
  content: string;
}

export interface SendChatOptions {
  history?: HistoryTurn[];
  userId?: number;
}

export interface FetchWelcomeOptions {
  userId?: number;
  provider?: "llama" | "chatgpt" | "auto";
}

/**
 * Get the full URL for an API endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.baseURL}${endpoint}`;
};

/**
 * Send a chat message to the backend API
 */
export const sendChatMessage = async (
  message: string,
  provider: "llama" | "chatgpt" = "chatgpt",
  options?: SendChatOptions
): Promise<string> => {
  const url = getApiUrl(API_CONFIG.endpoints.chat);
  // #region agent log
  fetch("http://127.0.0.1:7244/ingest/d0b8079a-06bd-45a0-8a12-196e313fff53", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ location: "api.ts:sendChatMessage", message: "fetch start", data: { url, messageLen: (message || "").length }, timestamp: Date.now(), hypothesisId: "H1" }) }).catch(() => {});
  // #endregion
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        provider,
        user_id: options?.userId,
        history: options?.history ?? [],
      }),
    });
  } catch (networkErr) {
    // #region agent log
    fetch("http://127.0.0.1:7244/ingest/d0b8079a-06bd-45a0-8a12-196e313fff53", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ location: "api.ts:sendChatMessage", message: "fetch failed", data: { error: String((networkErr as Error).message), name: (networkErr as Error).name }, timestamp: Date.now(), hypothesisId: "H1" }) }).catch(() => {});
    // #endregion
    throw networkErr;
  }
  // #region agent log
  fetch("http://127.0.0.1:7244/ingest/d0b8079a-06bd-45a0-8a12-196e313fff53", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ location: "api.ts:sendChatMessage", message: "response received", data: { ok: response.ok, status: response.status }, timestamp: Date.now(), hypothesisId: "H2" }) }).catch(() => {});
  // #endregion
  if (!response.ok) {
    let message = `HTTP error! status: ${response.status}`;
    try {
      const errBody = await response.clone().json() as { detail?: string };
      if (typeof errBody?.detail === "string" && errBody.detail) {
        message = errBody.detail;
      }
    } catch {
      // ignore parse failure; use status message
    }
    throw new Error(message);
  }
  let data: { response?: string; meta?: { intent?: string; used_provider?: string; fallback_used?: boolean } };
  try {
    data = await response.json();
  } catch (parseErr) {
    // #region agent log
    fetch("http://127.0.0.1:7244/ingest/d0b8079a-06bd-45a0-8a12-196e313fff53", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ location: "api.ts:sendChatMessage", message: "response.json failed", data: { error: String((parseErr as Error).message) }, timestamp: Date.now(), hypothesisId: "H3" }) }).catch(() => {});
    // #endregion
    throw parseErr;
  }
  // #region agent log
  fetch("http://127.0.0.1:7244/ingest/d0b8079a-06bd-45a0-8a12-196e313fff53", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ location: "api.ts:sendChatMessage", message: "body parsed", data: { hasResponseKey: "response" in data, responseType: typeof data?.response }, timestamp: Date.now(), hypothesisId: "H3" }) }).catch(() => {});
  // #endregion
  return data.response as string;
};

export const fetchWelcomeMessage = async (
  options?: FetchWelcomeOptions
): Promise<string> => {
  const url = getApiUrl(API_CONFIG.endpoints.welcome);
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: options?.userId,
      provider: options?.provider ?? "chatgpt",
    }),
  });

  if (!response.ok) {
    let message = `HTTP error! status: ${response.status}`;
    try {
      const errBody = await response.clone().json() as { detail?: string };
      if (typeof errBody?.detail === "string" && errBody.detail) {
        message = errBody.detail;
      }
    } catch {
      // ignore parse failure
    }
    throw new Error(message);
  }

  const data = await response.json() as { message?: string };
  if (!data?.message) {
    throw new Error("Welcome response missing message.");
  }
  return data.message;
};
