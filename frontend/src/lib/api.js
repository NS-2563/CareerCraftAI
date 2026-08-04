import axios from "axios";
import { API_BASE_URL, REQUEST_TIMEOUT, RETRY_CONFIG } from "@/config/environment";
import { normalizeError } from "@/utils/apiErrorHandler";
import { authService } from "@/services/authService";

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

let _isRefreshing = false;
let _failedQueue = [];

function _processQueue(error, token = null) {
  for (const { resolve, reject } of _failedQueue) {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  }
  _failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    // Don't intercept auth endpoints (login, register, refresh, logout)
    if (originalRequest.url?.includes("/api/auth/")) {
      return Promise.reject(error);
    }

    const status = error.response?.status;

    // --- 401 handling: refresh token and retry ---
    if (status === 401 && !originalRequest._retry401) {
      if (_isRefreshing) {
        return new Promise((resolve, reject) => {
          _failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry401 = true;
      _isRefreshing = true;

      try {
        await authService.refreshToken();
        const newToken = authService.getAccessToken();
        _processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch {
        _processQueue(error, null);
        return Promise.reject(error);
      } finally {
        _isRefreshing = false;
      }
    }

    // --- 5xx retry (existing behavior) ---
    const normalized = normalizeError(error);

    if (normalized.retryable && !originalRequest._retry5xx) {
      originalRequest._retry5xx = true;

      let retries = 0;
      const maxRetries = RETRY_CONFIG.maxRetries;

      while (retries < maxRetries) {
        try {
          await new Promise((resolve) =>
            setTimeout(resolve, RETRY_CONFIG.retryDelay * (retries + 1))
          );
          return await apiClient.request(originalRequest);
        } catch (retryError) {
          retries++;
          if (retries >= maxRetries) {
            throw retryError;
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

export { apiClient, withRetry };
export default apiClient;
