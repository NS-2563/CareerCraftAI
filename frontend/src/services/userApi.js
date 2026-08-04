import { apiClient } from "@/lib/api";
import { normalizeError } from "@/utils/apiErrorHandler";

const userApi = {
  async getProfile() {
    try {
      const res = await apiClient.get("/api/user/profile");
      return { success: true, data: res.data };
    } catch (error) {
      console.error("getProfile API error:", error);
      return { success: false, error: normalizeError(error).message };
    }
  },

  async updateProfile(data) {
    try {
      const res = await apiClient.put("/api/user/profile", data);
      return { success: true, data: res.data };
    } catch (error) {
      console.error("updateProfile API error:", error);
      return { success: false, error: normalizeError(error).message };
    }
  },

  async exportData() {
    try {
      const res = await apiClient.get("/api/user/data");
      return { success: true, data: res.data };
    } catch (error) {
      console.error("exportData API error:", error);
      return { success: false, error: normalizeError(error).message };
    }
  },

  async deleteAccount() {
    try {
      await apiClient.delete("/api/user/profile");
      return { success: true, data: { message: "Account deleted" } };
    } catch (error) {
      console.error("deleteAccount API error:", error);
      return { success: false, error: normalizeError(error).message };
    }
  },

  async changePassword({ current_password, new_password }) {
    try {
      await apiClient.post("/api/auth/change-password", {
        current_password,
        new_password,
      });
      return { success: true, data: { message: "Password changed" } };
    } catch (error) {
      console.error("changePassword API error:", error);
      return { success: false, error: normalizeError(error).message };
    }
  },

  async logoutAll() {
    try {
      await apiClient.post("/api/auth/logout-all");
      return { success: true, data: { message: "Logged out of all devices" } };
    } catch (error) {
      console.error("logoutAll API error:", error);
      return { success: false, error: normalizeError(error).message };
    }
  },
};

export default userApi;
