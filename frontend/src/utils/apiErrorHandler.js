import { RETRY_CONFIG } from "@/config/environment";

function isRetryableStatusCode(status) {
  return RETRY_CONFIG.retryableStatusCodes.includes(status);
}

function isNetworkError(error) {
  return (
    error.code === "ECONNABORTED" ||
    error.code === "ERR_NETWORK" ||
    !error.response
  );
}

function normalizeError(error) {
  const status = error.response?.status;
  const originalMessage = error.message || "An error occurred";

  let message = originalMessage;
  let retryable = false;

  if (error.response) {
    switch (status) {
      case 400:
        message = error.response.data?.detail || "Invalid request";
        break;
      case 401:
        message = "Authentication required";
        break;
      case 403:
        message = "Access denied";
        break;
      case 404:
        message = "Resource not found";
        break;
      case 422:
        message = error.response.data?.detail || "Validation error";
        break;
      case 500:
        message = "Server error";
        retryable = true;
        break;
      case 502:
      case 503:
      case 504:
        message = "Service temporarily unavailable";
        retryable = true;
        break;
      default:
        message = originalMessage;
        retryable = isRetryableStatusCode(status);
    }
  } else if (isNetworkError(error)) {
    message = "Network error. Please check your connection.";
    retryable = true;
  } else if (error.code === "ECONNABORTED") {
    message = "Request timed out";
    retryable = true;
  }

  let code = "UNKNOWN";
  if (status === 400) code = "VALIDATION_ERROR";
  else if (status === 401) code = "AUTH_REQUIRED";
  else if (status === 403) code = "FORBIDDEN";
  else if (status === 404) code = "NOT_FOUND";
  else if (status === 422) code = "VALIDATION_ERROR";
  else if (status >= 500) code = "SERVER_ERROR";
  else if (isNetworkError(error)) code = "NETWORK_ERROR";
  else if (error.code === "ECONNABORTED") code = "TIMEOUT";

  return {
    message,
    status,
    code,
    retryable,
    original: error,
  };
}

class ApiError extends Error {
  constructor(normalizedError) {
    super(normalizedError.message);
    this.name = "ApiError";
    this.status = normalizedError.status;
    this.code = normalizedError.code;
    this.retryable = normalizedError.retryable;
    this.original = normalizedError.original;
  }
}

export { normalizeError, ApiError, isRetryableStatusCode };
export default { normalizeError, ApiError, isRetryableStatusCode };

