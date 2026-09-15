import React from "react";
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
  }));

  return (
    <div className="glass-card chart-card">
      <div className="chart-header">
        <div>
          <div className="chart-title">Real-Time Telemetry Trend</div>
          <div className="chart-subtitle">Live rolling buffer (Utilization, VRAM, Temperature)</div>
        </div>
        <div className="chart-legend">
          <span className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: "#06b6d4" }} /> GPU Util (%)
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: "#6366f1" }} /> VRAM (%)
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: "#f59e0b" }} /> Temp (?C)
          </span>
        </div>
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
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0d1322",
                borderColor: "#1e293b",
                borderRadius: "8px",
                color: "#f8fafc",
                fontSize: "12px",
                boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
              }}
            />
            <Area
              type="monotone"
              dataKey="gpu"
              stroke="#06b6d4"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#gpuGrad)"
              name="GPU Utilization"
            />
            <Area
              type="monotone"
              dataKey="vram"
              stroke="#6366f1"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#vramGrad)"
              name="VRAM %"
            />
            <Area
              type="monotone"
              dataKey="temp"
              stroke="#f59e0b"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#tempGrad)"
              name="Temp (?C)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
