import { create } from "zustand";
import { logout as apiLogout } from "@/lib/api/auth";

interface AuthState {
  hydrated: boolean;
  hydrate: () => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  hydrated: false,

  hydrate: () => {
    // ✅ 쿠키는 HttpOnly라 JS로 읽을 수 없음
    // 그래서 프론트 hydration 의미만 살려둠
    set({ hydrated: true });
  },

  logout: async () => {
    try {
      await apiLogout(); // ✅ 서버 쿠키 삭제 + refresh revoke
    } finally {
      set({ hydrated: true });
      // accessToken/tenantId 같은 상태 자체가 없으니 따로 set 필요 없음
    }
  },
}));
