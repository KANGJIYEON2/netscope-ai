"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api/auth";

export default function RegisterPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    try {
      setLoading(true);
      setError(null);

      await register({ email, password }); // ✅ 쿠키 저장됨(백엔드)
      router.push("/projects");
    } catch (e: any) {
      // 백엔드에서 409(이메일 중복) 처리했으면 여기서 메시지 분기 가능
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
