"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { FolderGit2, Plus, ArrowUpRight } from "lucide-react";

import { fetchProjects, ProjectItem } from "@/lib/api/project";
import { AppShell } from "@/app/components/Layout/AppShell";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
  }, []);

  return (
    <AppShell>
      <main className="relative mx-auto max-w-5xl px-6 py-8">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-2.5 text-cyan-400">
              <FolderGit2 size={22} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Projects</h1>
              <p className="text-xs text-zinc-500">
                프로젝트를 선택해 진단 대시보드로 이동하세요.
              </p>
            </div>
          </div>
          <Link
            href="/projects/new"
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-500 px-4 py-2 text-sm font-semibold text-zinc-950 transition-opacity hover:opacity-90"
          >
            <Plus size={16} /> New Project
          </Link>
        </header>

        <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {loading &&
            Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900/40"
              />
            ))}

          {!loading && projects.length === 0 && (
            <div className="col-span-full flex flex-col items-center gap-3 rounded-2xl border border-dashed border-zinc-800 py-16 text-center">
              <FolderGit2 size={30} className="text-zinc-600" />
              <p className="text-sm text-zinc-400">아직 프로젝트가 없습니다.</p>
              <Link
                href="/projects/new"
                className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-700"
              >
                + 첫 프로젝트 만들기
              </Link>
            </div>
          )}

          {!loading &&
            projects.map((p, i) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06, duration: 0.4 }}
              >
                <Link
                  href={`/projects/${p.id}`}
                  className="group flex items-center justify-between rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 transition-colors hover:border-cyan-700/60 hover:bg-zinc-900"
                >
                  <div>
                    <h2 className="text-lg font-semibold text-zinc-100">
                      {p.name}
                    </h2>
                    <p className="mt-1 text-xs text-zinc-500">
                      created {new Date(p.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <ArrowUpRight
                    size={20}
                    className="text-zinc-600 transition-colors group-hover:text-cyan-400"
                  />
                </Link>
              </motion.div>
            ))}
        </section>
      </main>
    </AppShell>
  );
}
