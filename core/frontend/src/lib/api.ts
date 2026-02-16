/**
 * API Configuration
 * This file contains the API endpoint configuration for the backend server.
 * The backend server should be running on http://localhost:8000
 * Start it from core: cd core/backend/Response && uvicorn mainTry:app --reload --port 8000
 */

export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  endpoints: {
    chat: "/chat",
  },
} as const;

/**
 * Get the full URL for an API endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.baseURL}${endpoint}`;
};

/**
 * Send a chat message to the backend API
 */
export const sendChatMessage = async (message: string, provider?: "llama" | "chatgpt"): Promise<string> => {
  const response = await fetch(getApiUrl(API_CONFIG.endpoints.chat), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, provider }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.response;
};
