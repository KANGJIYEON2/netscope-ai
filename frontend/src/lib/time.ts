/** Compact relative-time formatter for live feeds ("3m ago"). */
export function timeAgo(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const diff = Math.max(0, Date.now() - t);
  const s = Math.floor(diff / 1000);
  if (s < 5) return "방금";
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}

/** First rule id token from a matched-rules label like "R005 ERROR … (+0.20)". */
export function ruleIdOf(label: string): string {
  return label.match(/^R\d+/)?.[0] ?? label.split(" ")[0];
}
