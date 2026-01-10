import axios from "axios";
import { API_BASE_URL } from "@/lib/config";
import { useAuthStore } from "@/lib/store/authStore";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

/* =========================
 * Request Interceptor
 * ========================= */
apiClient.interceptors.request.use((config) => {
  const { accessToken, tenantId } = useAuthStore.getState();

  console.log("🔥 INTERCEPTOR HIT", {
    url: config.url,
    accessToken,
    tenantId,
  });

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  if (tenantId) {
    config.headers["X-Tenant-ID"] = tenantId;
  }

  return config;
});

/* =========================
 * Response Interceptor
 * ========================= */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("⚠️ 401 Unauthorized → logout");

      const { logout } = useAuthStore.getState();
      logout();

      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
    }

    return Promise.reject(error);
  }
);
