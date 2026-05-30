import type { ReactNode } from "react";

/** Shared glass card used across dashboard + project tabs. */
export function Card({
  title,
  icon,
  action,
  children,
  className = "",
}: {
  title?: string;
  icon?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={
        "rounded-2xl border border-zinc-800/80 bg-zinc-900/40 p-5 backdrop-blur-sm " +
        className
      }
    >
      {(title || action) && (
        <div className="mb-4 flex items-center gap-2">
          {icon}
          {title && (
            <h3 className="text-sm font-semibold text-zinc-200">{title}</h3>
          )}
          {action && <div className="ml-auto">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
