import React from "react";

export function MetricCard({
  title,
  value,
  unit = "",
  subtext,
  icon: Icon,
  progress,
  color = "cyan",
  status = "normal"
}) {
  const colorMap = {
    cyan: "#06b6d4",
    indigo: "#6366f1",
    emerald: "#10b981",
    amber: "#f59e0b",
    rose: "#f43f5e",
  };

  const activeColor = colorMap[color] || "#06b6d4";

  return (
    <div className={`glass-card metric-card status-${status}`}>
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {Icon && (
          <div className="metric-icon-wrap" style={{ color: activeColor }}>
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="metric-body">
        <div className="metric-value-row">
          <span className="metric-value">
            {value !== null && value !== undefined ? value : "?"}
          </span>
          {unit && <span className="metric-unit">{unit}</span>}
        </div>
        {subtext && <div className="metric-subtext">{subtext}</div>}
      </div>

      {progress !== undefined && progress !== null && (
        <div className="metric-progress-track">
          <div
            className="metric-progress-bar"
            style={{
              width: `${Math.min(100, Math.max(0, progress))}%`,
              backgroundColor: activeColor,
            }}
          />
        </div>
      )}
    </div>
  );
}
