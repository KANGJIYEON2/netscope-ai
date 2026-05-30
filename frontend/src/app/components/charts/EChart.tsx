"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";

/**
 * Framework-agnostic ECharts wrapper (no React-binding package).
 *
 * echarts core is plain JS, so this stays compatible with React 19 / Next 16
 * where some chart libraries hit peer-dependency walls. We own the lifecycle:
 * init on mount, setOption on change, ResizeObserver for responsiveness,
 * dispose on unmount.
 */
export function EChart({
  option,
  height = 280,
  className,
  notMerge = true,
}: {
  option: EChartsOption;
  height?: number | string;
  className?: string;
  notMerge?: boolean;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  // Init / dispose once.
  useEffect(() => {
    if (!hostRef.current) return;
    const chart = echarts.init(hostRef.current, undefined, {
      renderer: "canvas",
    });
    chartRef.current = chart;

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(hostRef.current);

    return () => {
      ro.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  // Re-render on option change.
  useEffect(() => {
    chartRef.current?.setOption(option, notMerge);
  }, [option, notMerge]);

  return (
    <div
      ref={hostRef}
      className={className}
      style={{ width: "100%", height }}
    />
  );
}
