import React, { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

export function MetricsChart({ history }) {
  const [activeTab, setActiveTab] = useState("all");

  if (!history || history.length < 2) {
    return (
      <div className="glass-card chart-card flex-center">
        <span className="text-muted">Accumulating real-time telemetry stream...</span>
      </div>
    );
  }

  const chartData = history.map((item) => ({
    time: item.timeStr,
    gpu: item.gpu_utilization ?? 0,
    vram: item.memory_utilization ?? 0,
    temp: item.temperature ?? 0,
    cpu: item.cpu_utilization ?? 0,
    power: item.power_usage ?? 0,
  }));

  return (
    <div className="glass-card chart-card">
      <div className="chart-header">
        <div>
          <div className="chart-title">Real-Time Telemetry Trend (Phase 8 Multi-Stream)</div>
          <div className="chart-subtitle">Live rolling buffer with selective stream inspection</div>
        </div>

        {/* View mode toggle tabs */}
        <div className="chart-tab-group">
          <button
            className={`chart-tab ${activeTab === "all" ? "active" : ""}`}
            onClick={() => setActiveTab("all")}
          >
            Core View
          </button>
          <button
            className={`chart-tab ${activeTab === "cpu_power" ? "active" : ""}`}
            onClick={() => setActiveTab("cpu_power")}
          >
            CPU & Power
          </button>
        </div>
      </div>

      <div className="chart-legend">
        {activeTab === "all" ? (
          <>
            <span className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: "#06b6d4" }} /> GPU Util (%)
            </span>
            <span className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: "#6366f1" }} /> VRAM (%)
            </span>
            <span className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: "#f59e0b" }} /> Temp (°C)
            </span>
          </>
        ) : (
          <>
            <span className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: "#10b981" }} /> Host CPU Load (%)
            </span>
            <span className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: "#fbbf24" }} /> Power Draw (W)
            </span>
          </>
        )}
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gpuGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="vramGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="powerGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#fbbf24" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(13, 20, 36, 0.95)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#f1f5f9"
              }}
            />

            {activeTab === "all" ? (
              <>
                <Area type="monotone" dataKey="gpu" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#gpuGrad)" name="GPU Util (%)" />
                <Area type="monotone" dataKey="vram" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#vramGrad)" name="VRAM (%)" />
                <Area type="monotone" dataKey="temp" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#tempGrad)" name="Temp (°C)" />
              </>
            ) : (
              <>
                <Area type="monotone" dataKey="cpu" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#cpuGrad)" name="Host CPU (%)" />
                <Area type="monotone" dataKey="power" stroke="#fbbf24" strokeWidth={2} fillOpacity={1} fill="url(#powerGrad)" name="Power (W)" />
              </>
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
