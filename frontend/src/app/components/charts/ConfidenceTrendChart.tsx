"use client";

import { useMemo } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";

import { EChart } from "./EChart";
import { CONFIDENCE_THRESHOLDS, type TrendPoint } from "@/lib/api/report";

/**
 * Confidence-over-time area line.
 * - vertical gradient fill (cyan→transparent)
 * - glowing stroke (shadowBlur)
 * - dashed threshold markLines at 0.45 (warn) / 0.75 (high)
 * - bubble symbols whose size scales with that day's report_count
 */
export function ConfidenceTrendChart({
  points,
  height = 300,
}: {
  points: TrendPoint[];
  height?: number;
}) {
  const option = useMemo<EChartsOption>(() => {
    const dates = points.map((p) => p.date);
    const values = points.map((p) => p.avg_confidence);
    const counts = points.map((p) => p.report_count);
    const maxCount = Math.max(1, ...counts);

    return {
      backgroundColor: "transparent",
      grid: { top: 24, right: 18, bottom: 28, left: 40 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(9,9,11,0.92)",
        borderColor: "#3f3f46",
        borderWidth: 1,
        textStyle: { color: "#e4e4e7", fontSize: 12 },
        axisPointer: {
          type: "line",
          lineStyle: { color: "#52525b", type: "dashed" },
        },
        formatter: (params: unknown) => {
          const arr = params as Array<{
            dataIndex: number;
            axisValue: string;
            value: number;
          }>;
          const p = arr[0];
          const pct = Math.round(p.value * 100);
          return `
            <div style="font-weight:600;margin-bottom:4px">${p.axisValue}</div>
            <div>confidence&nbsp;<b style="color:#22d3ee">${pct}%</b></div>
            <div style="color:#a1a1aa">reports&nbsp;${counts[p.dataIndex]}</div>
          `;
        },
      },
      xAxis: {
        type: "category",
        data: dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: "#3f3f46" } },
        axisLabel: {
          color: "#71717a",
          fontSize: 11,
          formatter: (v) => String(v).slice(5), // MM-DD
        },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 1,
        interval: 0.25,
        axisLabel: {
          color: "#71717a",
          fontSize: 11,
          formatter: (v) => `${Math.round(Number(v) * 100)}%`,
        },
        splitLine: { lineStyle: { color: "rgba(63,63,70,0.4)", type: "dashed" } },
      },
      series: [
        {
          name: "confidence",
          type: "line",
          data: values,
          smooth: 0.4,
          symbol: "circle",
          symbolSize: (_v, p) =>
            6 + (counts[(p as { dataIndex: number }).dataIndex] / maxCount) * 14,
          showSymbol: true,
          itemStyle: {
            color: "#22d3ee",
            borderColor: "#0e7490",
            borderWidth: 1.5,
          },
          lineStyle: {
            width: 3,
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: "#67e8f9" },
              { offset: 0.5, color: "#22d3ee" },
              { offset: 1, color: "#a78bfa" },
            ]),
            shadowColor: "rgba(34,211,238,0.55)",
            shadowBlur: 18,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(34,211,238,0.45)" },
              { offset: 0.6, color: "rgba(34,211,238,0.10)" },
              { offset: 1, color: "rgba(34,211,238,0)" },
            ]),
          },
          emphasis: { focus: "series", scale: 1.2 },
          markLine: {
            silent: true,
            symbol: "none",
            label: {
              color: "#a1a1aa",
              fontSize: 10,
              formatter: (p) => `${Math.round(Number(p.value) * 100)}%`,
            },
            data: [
              {
                yAxis: CONFIDENCE_THRESHOLDS.high,
                lineStyle: { color: "#f87171", type: "dotted", width: 1.5 },
              },
              {
                yAxis: CONFIDENCE_THRESHOLDS.warn,
                lineStyle: { color: "#fbbf24", type: "dashed", width: 1.5 },
              },
            ],
          },
          animationDuration: 900,
          animationEasing: "cubicOut",
        },
      ],
    };
  }, [points]);

  return <EChart option={option} height={height} />;
}
