import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  tenantId: string | null;
  hydrated: boolean;

  login: (token: string, tenantId: string) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  tenantId: null,
  hydrated: false,

  hydrate: () => {
    if (typeof window === "undefined") return;

    const token = localStorage.getItem("accessToken");
    const tenantId = localStorage.getItem("tenantId");

    set({
      accessToken: token,
      tenantId,
      hydrated: true,
    });
  },

  login: (token, tenantId) => {
    localStorage.setItem("accessToken", token);
    localStorage.setItem("tenantId", tenantId);

    set({
      accessToken: token,
      tenantId,
    });
  },

  logout: () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("tenantId");

    set({
      accessToken: null,
      tenantId: null,
      hydrated: true, // ❗ 로그아웃해도 hydration 상태는 유지
    });
  },
}));
