"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { LayoutGrid, ScrollText, Activity, Brain, ChevronLeft } from "lucide-react";

import { fetchProjects } from "@/lib/api/project";
import { AppShell } from "@/app/components/Layout/AppShell";

export default function ProjectLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const pathname = usePathname() || "";
  const projectId = params?.projectId as string;
  const [name, setName] = useState<string>("");

  useEffect(() => {
    fetchProjects()
      .then((ps) => setName(ps.find((p) => p.id === projectId)?.name ?? ""))
      .catch(() => setName(""));
  }, [projectId]);

  const base = `/projects/${projectId}`;
  const tabs = [
    { href: base, label: "Overview", icon: LayoutGrid, exact: true },
    { href: `${base}/logs`, label: "Logs", icon: ScrollText },
    { href: `${base}/analyses`, label: "Analyses", icon: Activity },
    { href: `${base}/patterns`, label: "Patterns", icon: Brain },
  ];

  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname.startsWith(href);

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {/* Project header */}
        <header className="flex flex-wrap items-center gap-3">
          <Link
            href="/projects"
            className="flex items-center gap-1 text-xs text-zinc-500 transition-colors hover:text-zinc-300"
          >
            <ChevronLeft size={14} /> Projects
          </Link>
          <span className="text-zinc-700">/</span>
          <h1 className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-2xl font-bold text-transparent">
            {name || "Project"}
          </h1>
          <span className="ml-auto flex items-center gap-1.5 rounded-full border border-emerald-700/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            LIVE
          </span>
        </header>

        {/* Tab bar */}
        <nav className="mt-5 flex gap-1 border-b border-zinc-800">
          {tabs.map(({ href, label, icon: Icon, exact }) => {
            const active = isActive(href, exact);
            return (
              <Link
                key={href}
                href={href}
                className={
                  "relative flex items-center gap-2 px-4 py-2.5 text-sm transition-colors " +
                  (active
                    ? "font-semibold text-cyan-300"
                    : "text-zinc-400 hover:text-zinc-100")
                }
              >
                <Icon size={15} />
                {label}
                {active && (
                  <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-cyan-400" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Tab content */}
        <div className="mt-6">{children}</div>
      </div>
    </AppShell>
  );
}
