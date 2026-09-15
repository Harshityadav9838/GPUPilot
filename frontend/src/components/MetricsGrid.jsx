import React from "react";
import {
  Gauge,
  HardDrive,
  Thermometer,
  Zap,
  Cpu,
  Send
} from "lucide-react";
import { MetricCard } from "./MetricCard";

export function MetricsGrid({ metrics }) {
  if (!metrics) {
    return <div className="loading-grid">Awaiting GPU telemetry stream...</div>;
  }

  const utilStatus = metrics.gpu_utilization > 90 ? "warning" : "normal";
  const tempStatus = metrics.temperature > 82 ? "danger" : metrics.temperature > 75 ? "warning" : "normal";
  const vramStatus = metrics.memory_utilization > 90 ? "danger" : "normal";

  return (
    <div className="metrics-grid">
      {/* 1. GPU Utilization */}
      <MetricCard
        title="GPU Utilization"
        value={metrics.gpu_utilization}
        unit="%"
        subtext={`Clock: ${metrics.gpu_clock ? metrics.gpu_clock + ' MHz' : '?'}`}
        icon={Gauge}
        progress={metrics.gpu_utilization}
        color={metrics.gpu_utilization > 85 ? "amber" : "cyan"}
        status={utilStatus}
      />

      {/* 2. VRAM Usage */}
      <MetricCard
        title="VRAM Allocation"
        value={metrics.memory_used}
        unit={`/ ${metrics.memory_total} GB`}
        subtext={`${metrics.memory_utilization}% Utilized`}
        icon={HardDrive}
        progress={metrics.memory_utilization}
        color={metrics.memory_utilization > 90 ? "rose" : "indigo"}
        status={vramStatus}
      />

      {/* 3. Temperature */}
      <MetricCard
        title="Core Temperature"
        value={metrics.temperature}
        unit="°C"
        subtext={`Fan: ${metrics.fan_speed ? metrics.fan_speed + '%' : 'Auto'}`}
        icon={Thermometer}
        progress={metrics.temperature ? (metrics.temperature / 100) * 100 : 0}
        color={metrics.temperature > 82 ? "rose" : metrics.temperature > 72 ? "amber" : "emerald"}
        status={tempStatus}
      />

      {/* 4. Power Draw */}
      <MetricCard
        title="Power Draw"
        value={metrics.power_usage}
        unit="W"
        subtext={`Limit: ${metrics.power_limit ? metrics.power_limit + ' W' : '?'}`}
        icon={Zap}
        progress={metrics.power_limit && metrics.power_usage ? (metrics.power_usage / metrics.power_limit) * 100 : 0}
        color="amber"
      />

      {/* 5. Host CPU Utilization */}
      <MetricCard
        title="Host CPU Load"
        value={metrics.cpu_utilization}
        unit="%"
        subtext={metrics.cpu_utilization > 80 ? "High CPU contention" : "Nominal CPU load"}
        icon={Cpu}
        progress={metrics.cpu_utilization}
        color={metrics.cpu_utilization > 80 ? "rose" : metrics.cpu_utilization > 50 ? "amber" : "cyan"}
        status={metrics.cpu_utilization > 80 ? "warning" : "normal"}
      />

      {/* 6. Throughput */}
      <MetricCard
        title="Throughput"
        value={metrics.throughput}
        unit="req/s"
        subtext="Sustained batch throughput"
        icon={Send}
        color="emerald"
      />
    </div>
  );
}
