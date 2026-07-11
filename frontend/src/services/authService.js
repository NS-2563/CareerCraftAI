import { apiClient, setAuthToken, clearAuthToken } from "@/lib/api";

const AUTH_STORAGE_KEY = "careercraft_auth";

// Token storage helper
const getStoredAuth = () => {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
};

const setStoredAuth = (authData) => {
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
  } catch {
    console.error("Failed to store auth data");
  }
};

const clearStoredAuth = () => {
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch {
    console.error("Failed to clear auth data");
  }
};

// Auth service
export const authService = {
  // Login
  async login(email, password) {
    const response = await apiClient.post("/api/auth/login", { email, password });
    const { access_token, refresh_token, token_type } = response.data;

    setAuthToken(access_token);
    setStoredAuth({
      access_token,
      refresh_token,
      token_type,
    });

    // Get current user
    const userResponse = await apiClient.get("/api/auth/me");
    const user = userResponse.data;

    setStoredAuth({
      ...getStoredAuth(),
      user,
    });

    return user;
  },

  // Register
  async register(email, username, password) {
    await apiClient.post("/api/auth/register", {
      email,
      username,
      password,
    });

    // Auto-login after register
    return this.login(email, password);
  },

  // Logout
  logout() {
    clearAuthToken();
    clearStoredAuth();
  },

  // Refresh token
  async refreshToken() {
    const stored = getStoredAuth();
    if (!stored?.refresh_token) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await apiClient.post("/api/auth/refresh", null, {
        params: { refresh_token: stored.refresh_token },
      });

      const { access_token, refresh_token, token_type } = response.data;

      setAuthToken(access_token);
      setStoredAuth({
        access_token,
        refresh_token,
        token_type,
        user: stored.user,
      });

      return response.data;
    } catch (error) {
      this.logout();
      throw error;
    }
  },

  // Get current user
  async getCurrentUser() {
    const stored = getStoredAuth();
    if (!stored?.access_token) {
      return null;
    }

    setAuthToken(stored.access_token);

    try {
      const response = await apiClient.get("/api/auth/me");
      const user = response.data;

      // Update stored user
      setStoredAuth({
        ...stored,
        user,
      });

      return user;
    } catch {
      // Try to refresh token
      if (stored.refresh_token) {
        try {
          await this.refreshToken();
          const retryResponse = await apiClient.get("/api/auth/me");
          return retryResponse.data;
        } catch {
          this.logout();
          return null;
        }
      }
      this.logout();
      return null;
    }
  },

  // Restore session
  async restoreSession() {
    const stored = getStoredAuth();
    if (!stored?.access_token) {
      return null;
    }

    setAuthToken(stored.access_token);

    try {
      const response = await apiClient.get("/api/auth/me");
      return response.data;
    } catch {
      // Try to refresh
      if (stored.refresh_token) {
        try {
          await this.refreshToken();
          const response = await apiClient.get("/api/auth/me");
          return response.data;
        } catch {
          this.logout();
          return null;
        }
      }
      this.logout();
      return null;
    }
  },

  // Check if authenticated
  isAuthenticated() {
    const stored = getStoredAuth();
    return !!stored?.access_token;
  },

  // Get stored user
  getStoredUser() {
    const stored = getStoredAuth();
    return stored?.user || null;
  },
};

export default authService;