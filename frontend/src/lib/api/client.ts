import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL } from "@/lib/config";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // ⭐ 쿠키 기반 인증 필수
});

/* =========================
 * Request Interceptor
 * ========================= */
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // ✅ 이제 accessToken/tenantId를 프론트에서 들고있지 않음
  // ✅ Authorization / X-Tenant-ID 헤더도 프론트에서 붙이지 않음 (백엔드가 쿠키로 인증)
  return config;
});

/* =========================
 * Response Interceptor
 * ========================= */

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function runRefresh(): Promise<void> {
  // refresh는 쿠키로만 동작해야 함
  await apiClient.post("/auth/refresh");
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (!originalRequest || status !== 401) {
      return Promise.reject(error);
    }

    // ✅ 무한루프 방지
    if (originalRequest._retry) {
      // refresh까지 실패한 상태
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    try {
      // ✅ refresh는 동시 다발 호출되면 꼬이니 단일화
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = runRefresh().finally(() => {
          isRefreshing = false;
          refreshPromise = null;
        });
      }

      await refreshPromise;

      // ✅ refresh 성공했으니 원래 요청 재시도
      return apiClient(originalRequest);
    } catch (refreshErr) {
      // ✅ refresh 실패 → 로그인 페이지로
      try {
        await apiClient.post("/auth/logout"); // 쿠키 정리(백엔드가 이미 정리할 수도 있음)
      } catch (_) {
        // ignore
      }

      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
      return Promise.reject(refreshErr);
    }
  },
);
