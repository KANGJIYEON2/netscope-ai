"use client";

import { useRouter } from "next/navigation";
import { logout } from "@/lib/api/auth";

export default function LogoutButton() {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await logout(); // ✅ 서버에서 refresh revoke + 쿠키 삭제
    } catch (e) {
      console.error("logout failed", e);
    } finally {
      router.push("/auth/login");
    }
  };

  return (
    <button
      onClick={handleLogout}
      className="
        rounded px-3 py-2
        text-sm text-zinc-400
        hover:text-white hover:bg-zinc-800
      "
    >
      Logout
    </button>
  );
}
