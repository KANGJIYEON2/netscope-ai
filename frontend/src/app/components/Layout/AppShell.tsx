"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FolderGit2,
  FlaskConical,
  LogOut,
  Radar,
} from "lucide-react";

import { logout } from "@/lib/api/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FolderGit2 },
  { href: "/test-log", label: "Test Log", icon: FlaskConical },
];

/**
 * Persistent application shell — single source of navigation across every
 * authenticated page (replaces the per-page duplicated sidebars).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const router = useRouter();

  const isActive = (href: string) =>
    href === "/dashboard"
      ? pathname === "/dashboard"
      : pathname === href || pathname.startsWith(href + "/");

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      /* ignore */
    } finally {
      router.push("/auth/login");
    }
  };

  return (
    <div className="relative min-h-screen bg-zinc-950 text-zinc-100">
      {/* ambient background glows (shared across all pages) */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 top-0 h-96 w-96 rounded-full bg-cyan-600/10 blur-[120px]" />
        <div className="absolute right-0 top-1/3 h-96 w-96 rounded-full bg-violet-600/10 blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 h-96 w-96 rounded-full bg-fuchsia-600/5 blur-[120px]" />
      </div>

      <div className="relative flex">
        {/* Sidebar */}
        <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-zinc-800/80 bg-zinc-900/40 backdrop-blur-sm">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-5 py-5"
          >
            <span className="rounded-lg bg-gradient-to-br from-cyan-500 to-violet-500 p-1.5 text-zinc-950">
              <Radar size={18} />
            </span>
            <span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text font-bold tracking-tight text-transparent">
              NETSCOPE&nbsp;AI
            </span>
          </Link>

          <nav className="flex-1 space-y-1 px-3">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors " +
                    (active
                      ? "bg-zinc-800/80 font-semibold text-cyan-300"
                      : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100")
                  }
                >
                  <Icon size={17} />
                  {label}
                  {active && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-zinc-800/80 p-3">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-400 transition-colors hover:bg-zinc-800/50 hover:text-rose-300"
            >
              <LogOut size={17} />
              Logout
            </button>
          </div>
        </aside>

        {/* Main */}
        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </div>
  );
}
