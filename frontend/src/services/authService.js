import { apiClient, setAuthToken, clearAuthToken } from "@/lib/api";

let currentUser = null;
let accessToken = null;

export const authService = {
  async login(email, password) {
    const response = await apiClient.post("/api/auth/login", { email, password });
    const { access_token, token_type } = response.data;

    accessToken = access_token;
    setAuthToken(access_token);

    const userResponse = await apiClient.get("/api/auth/me");
    currentUser = userResponse.data;

    return currentUser;
  },

  async register(email, username, password) {
    await apiClient.post("/api/auth/register", { email, username, password });
    return this.login(email, password);
  },

  async logout() {
    try {
      await apiClient.post("/api/auth/logout");
    } catch {
      // Ignore errors — still clear local state
    }
    clearAuthToken();
    accessToken = null;
    currentUser = null;
  },

  async refreshToken() {
    try {
      const response = await apiClient.post("/api/auth/refresh");
      const { access_token } = response.data;

      accessToken = access_token;
      setAuthToken(access_token);

      return response.data;
    } catch (error) {
      await this.logout();
      throw error;
    }
  },

  async getCurrentUser() {
    if (!accessToken) {
      return null;
    }

    setAuthToken(accessToken);

    try {
      const response = await apiClient.get("/api/auth/me");
      currentUser = response.data;
      return currentUser;
    } catch {
      try {
        await this.refreshToken();
        const retryResponse = await apiClient.get("/api/auth/me");
        currentUser = retryResponse.data;
        return currentUser;
      } catch {
        this.logout();
        return null;
      }
    }
  },

  async restoreSession() {
    try {
      await this.refreshToken();
      const response = await apiClient.get("/api/auth/me");
      currentUser = response.data;
      return currentUser;
    } catch {
      this.logout();
      return null;
    }
  },

  isAuthenticated() {
    return !!accessToken;
  },

  getStoredUser() {
    return currentUser;
  },

  getAccessToken() {
    return accessToken;
  },
};

export default authService;
