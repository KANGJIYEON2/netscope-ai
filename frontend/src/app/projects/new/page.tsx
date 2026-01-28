"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { createProject } from "@/lib/api/project";

export default function NewProjectPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!name.trim()) return;

    try {
      setLoading(true);
      await createProject(name.trim());
      router.push("/projects");
    } catch (e) {
      // ✅ 401이면 apiClient 인터셉터가 refresh 시도 후 실패 시 /auth/login 이동
      console.error("Failed to create project", e);
      alert("프로젝트 생성 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      {/* Left Nav */}
      <aside className="w-56 border-r border-zinc-800 p-4">
        <nav className="space-y-2">
          <Link
            href="/projects"
            className="block rounded px-3 py-2 text-sm bg-zinc-800 text-white"
          >
            Project Log
          </Link>
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 max-w-md mx-auto p-6 space-y-6">
        <header>
          <h1 className="text-2xl font-bold">New Project</h1>
          <p className="text-sm text-zinc-400">
            Create a new project for log analysis
          </p>
        </header>

        <div className="space-y-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Project name"
            className="
              w-full rounded bg-zinc-900 border border-zinc-700
              px-3 py-2 text-sm
              focus:outline-none focus:border-white
            "
          />

          <button
            onClick={submit}
            disabled={loading}
            className="
              w-full py-2 rounded
              bg-white text-black font-semibold
              hover:bg-zinc-200
              disabled:opacity-50
            "
          >
            {loading ? "Creating..." : "Create Project"}
          </button>
        </div>
      </main>
    </div>
  );
}
