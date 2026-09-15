import React, { useState } from "react";
import { AlertTriangle, CheckCircle, ShieldAlert, Sparkles, ArrowRight, ChevronDown, ChevronUp } from "lucide-react";

const SEVERITY_COLORS = {
  ok:       "text-emerald",
  low:      "text-amber",
  medium:   "text-amber",
  high:     "text-rose",
  critical: "text-rose",
};

const BOTTLENECK_LABELS = {
  none:               "All Systems Nominal",
  thermal_throttling: "Thermal Throttling",
  vram_exhaustion:    "VRAM Exhaustion",
  compute_bound:      "Compute Bottleneck",
  cpu_starvation:     "CPU Starvation",
  memory_bandwidth:   "Memory Bandwidth",
  vram_pressure:      "VRAM Pressure",
  unknown:            "Unknown",
};

function MetricPill({ label, value, unit = "" }) {
  if (value === null || value === undefined) return null;
  return (
    <span className="metric-pill">
      <span className="metric-pill-label">{label}</span>
      <strong className="metric-pill-value">{typeof value === "number" ? value.toFixed(1) : value}{unit}</strong>
    </span>
  );
}

export function DiagnosticCard({ diagnosis }) {
  const [expanded, setExpanded] = useState(false);
  if (!diagnosis) return null;

  const isHealthy  = diagnosis.status === "healthy";
  const isCritical = diagnosis.status === "critical";
  const colorClass = SEVERITY_COLORS[diagnosis.severity] || "text-amber";
  const snap       = diagnosis.metrics_snapshot || {};

  const label = BOTTLENECK_LABELS[diagnosis.bottleneck] ||
                diagnosis.bottleneck.toUpperCase().replace(/_/g, " ");

  return (
    <div className={`glass-card diagnosis-card ${diagnosis.status}`}>
      {/* Header */}
      <div className="diagnosis-header">
        <div className="flex-row items-center gap-2">
          {isHealthy ? (
            <CheckCircle className="text-emerald" size={20} />
          ) : isCritical ? (
            <ShieldAlert className="text-rose" size={20} />
          ) : (
            <AlertTriangle className="text-amber" size={20} />
          )}
          <span className="diagnosis-title">Bottleneck Detection Engine</span>
        </div>
        <div className="diagnosis-confidence">
          Confidence: <strong>{Math.round(diagnosis.confidence * 100)}%</strong>
        </div>
      </div>

      {/* Detected State */}
      <div className="diagnosis-body">
        <div className="diagnosis-bottleneck">
          <span className="label">Detected State:</span>
          <span className={`tag-state ${diagnosis.status}`}>{label}</span>
          {diagnosis.severity && diagnosis.severity !== "ok" && (
            <span className={`severity-pill ${diagnosis.severity}`}>
              {diagnosis.severity.toUpperCase()}
            </span>
          )}
        </div>

        {/* Title */}
        {diagnosis.title && (
          <p className="diagnosis-title-text">{diagnosis.title}</p>
        )}

        {/* Explanation */}
        <p className="diagnosis-explanation">{diagnosis.explanation}</p>

        {/* Metrics snapshot pills */}
        {snap && Object.keys(snap).length > 0 && (
          <div className="snapshot-pills">
            <MetricPill label="GPU" value={snap.gpu_utilization} unit="%" />
            <MetricPill label="VRAM" value={snap.memory_utilization} unit="%" />
            <MetricPill label="Temp" value={snap.temperature} unit=" °C" />
            <MetricPill label="CPU" value={snap.cpu_utilization} unit="%" />
            <MetricPill label="Power" value={snap.power_usage} unit=" W" />
          </div>
        )}

        {/* Recommendations */}
        {diagnosis.recommendations && diagnosis.recommendations.length > 0 && (
          <div className="recommendations-box">
            <div className="rec-header">
              <Sparkles size={14} className="text-cyan" />
              <span>Prescriptions ({diagnosis.recommendations.length})</span>
            </div>
            <ul className="rec-list">
              {diagnosis.recommendations.map((rec, i) => (
                <li key={i} className="rec-item">
                  <ArrowRight size={14} className="rec-bullet" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
