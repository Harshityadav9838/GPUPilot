import React from "react";
import { AlertTriangle, CheckCircle, ShieldAlert, Sparkles, ArrowRight } from "lucide-react";

export function DiagnosticCard({ diagnosis }) {
  if (!diagnosis) return null;

  const isHealthy = diagnosis.status === "healthy";
  const isCritical = diagnosis.status === "critical";

  return (
    <div className={`glass-card diagnosis-card ${diagnosis.status}`}>
      <div className="diagnosis-header">
        <div className="flex-row items-center gap-2">
          {isHealthy ? (
            <CheckCircle className="text-emerald" size={20} />
          ) : isCritical ? (
            <ShieldAlert className="text-rose" size={20} />
          ) : (
            <AlertTriangle className="text-amber" size={20} />
          )}
          <span className="diagnosis-title">Autonomous Diagnosis Engine</span>
        </div>
        <div className="diagnosis-confidence">
          Confidence: <strong>{Math.round(diagnosis.confidence * 100)}%</strong>
        </div>
      </div>

      <div className="diagnosis-body">
        <div className="diagnosis-bottleneck">
          <span className="label">Detected State:</span>
          <span className={`tag-state ${diagnosis.status}`}>
            {diagnosis.bottleneck.toUpperCase().replace("_", " ")}
          </span>
        </div>
        <p className="diagnosis-explanation">{diagnosis.explanation}</p>

        {diagnosis.recommendations && diagnosis.recommendations.length > 0 && (
          <div className="recommendations-box">
            <div className="rec-header">
              <Sparkles size={14} className="text-cyan" />
              <span>Prescribed Optimization Actions</span>
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
