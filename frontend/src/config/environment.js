const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const USE_MOCK_AI = import.meta.env.VITE_USE_MOCK_AI === "true";

const REQUEST_TIMEOUT = 30000;

const RETRY_CONFIG = {
  maxRetries: 2,
  retryableStatusCodes: [502, 503, 504],
  retryDelay: 1000,
};

export {
  API_BASE_URL,
  USE_MOCK_AI,
  REQUEST_TIMEOUT,
  RETRY_CONFIG,
};