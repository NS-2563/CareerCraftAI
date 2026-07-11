import { useState, useCallback, useRef } from "react";

export default function useAI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);
  const abortControllerRef = useRef(null);

  const execute = useCallback(async (serviceFn, ...args) => {
    // Cancel any pending request before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setLoading(true);
    setError(null);

    try {
      // Create signal and pass at the end of args
      const signal = abortController.signal;
      const result = await serviceFn(...args, signal);

      // If request was cancelled, don't update state
      if (signal.aborted) {
        return null;
      }

      if (result.success) {
        setResponse(result.data);
        return result.data;
      } else {
        setError(result.error || "An error occurred");
        return null;
      }
    } catch (err) {
      // Ignore cancellation errors
      if (err.name === "CanceledError" || err.name === "AbortError") {
        return null;
      }
      const errorMessage = err.message || "Failed to execute AI action";
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  const clearResponse = useCallback(() => {
    setResponse(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    response,
    execute,
    clearResponse,
    clearError,
    cancel,
  };
}