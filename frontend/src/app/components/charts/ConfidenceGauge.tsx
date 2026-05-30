"use client";

import { useMemo } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";

import { EChart } from "./EChart";
import { confidenceHex } from "@/styles/severity";

/**
 * Radial confidence gauge (0..1). The progress arc is colored by the same
 * thresholds the rule engine uses (0.45 / 0.75 / 0.85) and glows.
 */
export function ConfidenceGauge({
  value,
  height = 200,
}: {
  value: number;
  height?: number;
}) {
  const option = useMemo<EChartsOption>(() => {
    const pct = Math.round(value * 100);
    const color = confidenceHex(value);

    return {
      backgroundColor: "transparent",
      series: [
        {
          type: "gauge",
          startAngle: 220,
          endAngle: -40,
          min: 0,
          max: 100,
          radius: "92%",
          center: ["50%", "56%"],
          pointer: { show: false },
          progress: {
            show: true,
            roundCap: true,
            width: 14,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                { offset: 0, color },
                { offset: 1, color: "#a78bfa" },
              ]),
              shadowColor: color,
              shadowBlur: 16,
            },
          },
          axisLine: {
            roundCap: true,
            lineStyle: { width: 14, color: [[1, "rgba(63,63,70,0.45)"]] },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          anchor: { show: false },
          title: {
            show: true,
            offsetCenter: [0, "34%"],
            color: "#71717a",
            fontSize: 12,
          },
          detail: {
            valueAnimation: true,
            offsetCenter: [0, "-2%"],
            formatter: `${pct}%`,
            color: color,
            fontSize: 34,
            fontWeight: 700,
          },
          data: [{ value: pct, name: "confidence" }],
        },
      ],
    };
  }, [value]);

  return <EChart option={option} height={height} />;
}
