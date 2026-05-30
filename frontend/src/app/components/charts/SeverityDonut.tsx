"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";

import { EChart } from "./EChart";
import type { Severity } from "@/types/analysis";
import { severityConfig, SEVERITY_ORDER } from "@/styles/severity";

/**
 * Severity distribution as a glowing doughnut with a centered total.
 */
export function SeverityDonut({
  counts,
  height = 220,
}: {
  counts: Record<Severity, number>;
  height?: number;
}) {
  const total = SEVERITY_ORDER.reduce((s, k) => s + (counts[k] ?? 0), 0);

  const option = useMemo<EChartsOption>(() => {
    const data = SEVERITY_ORDER.filter((s) => (counts[s] ?? 0) > 0).map((s) => ({
      name: severityConfig[s].label,
      value: counts[s],
      itemStyle: {
        color: severityConfig[s].hex,
        shadowColor: severityConfig[s].hex,
        shadowBlur: 12,
        borderColor: "#09090b",
        borderWidth: 3,
      },
    }));

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(9,9,11,0.92)",
        borderColor: "#3f3f46",
        textStyle: { color: "#e4e4e7", fontSize: 12 },
        formatter: "{b}<br/><b>{c}</b> ({d}%)",
      },
      series: [
        {
          type: "pie",
          radius: ["62%", "86%"],
          center: ["50%", "50%"],
          avoidLabelOverlap: false,
          label: { show: false },
          labelLine: { show: false },
          padAngle: 3,
          itemStyle: { borderRadius: 6 },
          data,
          animationType: "scale",
          animationEasing: "elasticOut",
          animationDuration: 800,
        },
      ],
      graphic: [
        {
          type: "text",
          left: "center",
          top: "42%",
          style: {
            text: String(total),
            fill: "#fafafa",
            fontSize: 30,
            fontWeight: 700,
          },
        },
        {
          type: "text",
          left: "center",
          top: "58%",
          style: {
            text: "analyses",
            fill: "#71717a",
            fontSize: 11,
          },
        },
      ],
    };
  }, [counts, total]);

  return <EChart option={option} height={height} />;
}
