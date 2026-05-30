import type { Severity } from "@/types/analysis";

/**
 * Severity → color mapping (single source of truth).
 * Tailwind classes assume dark theme on zinc-950 background.
 * Use *-400 / *-500 tones for visibility.
 */

export const severityConfig: Record<
  Severity,
  {
    label: string;
    bg: string;
    text: string;
    border: string;
    badge: string;
    /** Hex for canvas charts (ECharts) — keep in sync with the Tailwind tone. */
    hex: string;
    /** Lighter hex used as the top stop of area/glow gradients. */
    hexSoft: string;
    /** CSS gradient for hero / glow accents. */
    gradient: string;
  }
> = {
  LOW: {
    label: "Low",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500",
    badge: "bg-cyan-500/20 text-cyan-400",
    hex: "#22d3ee", // cyan-400
    hexSoft: "#67e8f9", // cyan-300
    gradient: "from-cyan-500/30 via-cyan-400/10 to-transparent",
  },
  MEDIUM: {
    label: "Medium",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500",
    badge: "bg-amber-500/20 text-amber-400",
    hex: "#fbbf24", // amber-400
    hexSoft: "#fcd34d", // amber-300
    gradient: "from-amber-500/30 via-amber-400/10 to-transparent",
  },
  HIGH: {
    label: "High",
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500",
    badge: "bg-red-500/20 text-red-400",
    hex: "#f87171", // red-400
    hexSoft: "#fca5a5", // red-300
    gradient: "from-red-500/30 via-red-400/10 to-transparent",
  },
  CRITICAL: {
    label: "Critical",
    bg: "bg-fuchsia-500/10",
    text: "text-fuchsia-400",
    border: "border-fuchsia-500",
    badge: "bg-fuchsia-500/20 text-fuchsia-400",
    hex: "#e879f9", // fuchsia-400
    hexSoft: "#f0abfc", // fuchsia-300
    gradient: "from-fuchsia-500/30 via-fuchsia-400/10 to-transparent",
  },
};

/** Order used for distributions/legends. */
export const SEVERITY_ORDER: Severity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

/** Normalize an arbitrary backend severity string to a known Severity. */
export function asSeverity(value: string | null | undefined): Severity {
  const v = (value ?? "").toUpperCase();
  return (SEVERITY_ORDER as string[]).includes(v) ? (v as Severity) : "LOW";
}

/** Hex for a confidence value, mirroring the engine's severity thresholds. */
export function confidenceHex(confidence: number): string {
  if (confidence >= 0.85) return severityConfig.CRITICAL.hex;
  if (confidence >= 0.75) return severityConfig.HIGH.hex;
  if (confidence >= 0.45) return severityConfig.MEDIUM.hex;
  return severityConfig.LOW.hex;
}

/** Get Tailwind border-left color class for card accents. */
export function severityBorderClass(severity: Severity): string {
  return `border-l-4 ${severityConfig[severity].border}`;
}

/** Get badge classes for inline severity chips. */
export function severityBadgeClass(severity: Severity): string {
  return `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${severityConfig[severity].badge}`;
}
