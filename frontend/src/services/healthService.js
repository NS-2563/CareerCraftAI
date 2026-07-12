import axios from "axios";
import { API_BASE_URL } from "@/config/environment";

export async function checkHealth() {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`, {
      timeout: 5000,
    });
    return {
      online: true,
      data: response.data,
    };
  } catch (error) {
    return {
      online: false,
      error: error.message,
    };
  }
}

export default { checkHealth };

