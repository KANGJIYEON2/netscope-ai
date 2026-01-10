"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { fetchProjects, ProjectItem } from "@/lib/api/project";
import { useAuthStore } from "@/lib/store/authStore";

export default function ProjectsPage() {
  const router = useRouter();

  // 🔐 Auth 상태 (JWT 기준)
  const { accessToken, hydrated, hydrate } = useAuthStore();

  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);

  // 1️⃣ hydration
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // 2️⃣ 인증 확인 + 프로젝트 로드
  useEffect(() => {
    if (!hydrated) return;

    if (!accessToken) {
      router.push("/auth/login");
      return;
    }

    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchProjects();
        setProjects(data);
      } catch (e) {
        console.error("Failed to load projects", e);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [hydrated, accessToken, router]);

  // 3️⃣ 로딩 상태
  if (!hydrated || loading) {
    return (
      <div className="flex h-screen items-center justify-center text-zinc-400">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      {/* ================= Left Navigation ================= */}
      <aside className="w-56 border-r border-zinc-800 p-4">
        <nav className="space-y-2">
          <Link
            href="/test-log"
            className="block rounded px-3 py-2 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-white"
          >
            Test Log
          </Link>

          <Link
            href="/projects"
            className="block rounded px-3 py-2 text-sm bg-zinc-800 text-white"
          >
            Project Log
          </Link>
        </nav>
      </aside>

      {/* ================= Main Content ================= */}
      <main className="relative flex-1 max-w-5xl mx-auto p-6 space-y-6">
        <header>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-sm text-zinc-400">
            Select a project to view analysis
          </p>
        </header>

        {/* ================= Project List ================= */}
        <section className="space-y-3">
          {projects.length === 0 && (
            <div className="rounded border border-dashed border-zinc-700 p-8 text-center text-zinc-400">
              <p className="text-sm font-medium">현재 로그가 없습니다</p>
              <p className="mt-1 text-xs text-zinc-500">
                새 프로젝트를 생성하거나 로그를 수집해보세요.
              </p>
            </div>
          )}

          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="
                block p-4 rounded
                border border-zinc-800
                bg-zinc-900 hover:bg-zinc-800
              "
            >
              <div className="flex justify-between items-center">
                <h2 className="font-semibold text-lg">{p.name}</h2>
                <span className="text-xs text-zinc-500">
                  {new Date(p.created_at).toLocaleDateString()}
                </span>
              </div>
            </Link>
          ))}
        </section>

        {/* ================= New Project Button ================= */}
        <Link
          href="/projects/new"
          className="
            fixed bottom-6 right-6
            flex items-center justify-center
            h-12 w-12 rounded-full
            bg-white text-black
            shadow-lg hover:bg-zinc-200
            text-2xl font-bold
          "
          title="New Project"
        >
          +
        </Link>
      </main>
    </div>
  );
}
