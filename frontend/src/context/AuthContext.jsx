import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import authService from "@/services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(authService.getStoredUser());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function restore() {
      try {
        const restoredUser = await authService.restoreSession();

        if (mounted) {
          setUser(restoredUser);
        }
      } catch {
        if (mounted) {
          setUser(null);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    restore();

    return () => {
      mounted = false;
    };
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    setError(null);

    try {
      const loggedInUser = await authService.login(email, password);
      setUser(loggedInUser);
      return loggedInUser;
    } catch (err) {
      setError(
        err?.response?.data?.detail ??
          err?.message ??
          "Login failed"
      );
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email, username, password) => {
    setIsLoading(true);
    setError(null);

    try {
      const newUser = await authService.register(
        email,
        username,
        password
      );

      setUser(newUser);
      return newUser;
    } catch (err) {
      setError(
        err?.response?.data?.detail ??
          err?.message ??
          "Registration failed"
      );
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      error,
      isLoading,
      login,
      register,
      logout,
      clearError,
      isAuthenticated: !!user,
    }),
    [
      user,
      error,
      isLoading,
      login,
      register,
      logout,
      clearError,
    ]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}/* eslint-disable react-refresh/only-export-components */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within an AuthProvider"
    );
  }

  return context;
}

