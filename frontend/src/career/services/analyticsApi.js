import api from "@/lib/api";

const analyticsApi = {
  getAnalytics() {
    return api.get("/career/analytics");
  },
};

export default analyticsApi;

