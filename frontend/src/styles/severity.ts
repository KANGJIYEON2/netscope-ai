import type { Severity } from "@/types/analysis";

/**
 * Severity → color mapping (single source of truth).
 * Tailwind classes assume dark theme on zinc-950 background.
 * Use *-400 / *-500 tones for visibility.
 */

export const severityConfig: Record<
  Severity,
  { label: string; bg: string; text: string; border: string; badge: string }
> = {
  LOW: {
    label: "Low",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500",
    badge: "bg-cyan-500/20 text-cyan-400",
  },
  MEDIUM: {
    label: "Medium",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500",
    badge: "bg-amber-500/20 text-amber-400",
  },
  HIGH: {
    label: "High",
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500",
    badge: "bg-red-500/20 text-red-400",
  },
  CRITICAL: {
    label: "Critical",
    bg: "bg-fuchsia-500/10",
    text: "text-fuchsia-400",
    border: "border-fuchsia-500",
    badge: "bg-fuchsia-500/20 text-fuchsia-400",
  },
};

/** Get Tailwind border-left color class for card accents. */
export function severityBorderClass(severity: Severity): string {
  return `border-l-4 ${severityConfig[severity].border}`;
}

/** Get badge classes for inline severity chips. */
export function severityBadgeClass(severity: Severity): string {
  return `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${severityConfig[severity].badge}`;
}
