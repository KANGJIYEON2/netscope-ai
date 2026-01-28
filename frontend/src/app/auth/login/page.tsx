"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);

      await login({ email, password }); // ✅ 쿠키 저장됨(백엔드)
      router.push("/projects");
    } catch {
      setError("로그인 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="text-xl font-bold mb-4 text-center">로그인</h1>

      <input
        className="w-full border p-2 mb-2"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        className="w-full border p-2 mb-4"
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      {error && <p className="text-sm text-red-500 mb-2">{error}</p>}

      <button
        onClick={handleLogin}
        disabled={loading}
        className="w-full bg-black text-white py-2"
      >
        {loading ? "로그인 중..." : "로그인"}
      </button>

      <p className="text-sm text-center mt-4">
        계정이 없나요?{" "}
        <a href="/auth/register" className="text-blue-600 underline">
          회원가입
        </a>
      </p>
    </>
  );
}
