"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const auth = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await register({ email, password });
      auth.login(res.access_token, res.tenant_id);

      router.push("/projects");
    } catch {
      setError("회원가입 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="text-xl font-bold mb-4 text-center">회원가입</h1>

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
        onClick={handleRegister}
        disabled={loading}
        className="w-full bg-black text-white py-2"
      >
        {loading ? "가입 중..." : "회원가입"}
      </button>

      <p className="text-sm text-center mt-4">
        이미 계정이 있나요?{" "}
        <a href="/auth/login" className="text-blue-600 underline">
          로그인
        </a>
      </p>
    </>
  );
}
