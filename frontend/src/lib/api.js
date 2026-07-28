import axios from "axios";
import { API_BASE_URL, REQUEST_TIMEOUT, RETRY_CONFIG } from "@/config/environment";
import { normalizeError } from "@/utils/apiErrorHandler";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function clearAuthToken() {
  authToken = null;
}

apiClient.interceptors.request.use(
  (config) => {
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

async function withRetry(requestFn) {
  let lastError = null;
  let retries = 0;

  while (retries <= RETRY_CONFIG.maxRetries) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      const normalized = normalizeError(error);

      if (!normalized.retryable || retries >= RETRY_CONFIG.maxRetries) {
        throw error;
      }

      retries++;
      await new Promise((resolve) =>
        setTimeout(resolve, RETRY_CONFIG.retryDelay * retries)
      );
    }
  }

  throw lastError;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const normalized = normalizeError(error);

    if (normalized.retryable) {
      const config = error.config;

      if (config && !config._retry) {
        config._retry = true;

        let retries = 0;
        const maxRetries = RETRY_CONFIG.maxRetries;

        while (retries < maxRetries) {
          try {
            await new Promise((resolve) =>
              setTimeout(resolve, RETRY_CONFIG.retryDelay * (retries + 1))
            );
            return await apiClient.request(config);
          } catch (retryError) {
            retries++;
            if (retries >= maxRetries) {
              throw retryError;
            }
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

export { apiClient, withRetry };
export default apiClient;
