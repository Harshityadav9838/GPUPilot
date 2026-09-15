import React from "react";
import { Sliders, CheckCircle2 } from "lucide-react";

export function ScenarioSelector({ scenarios, activeScenario, onSelect, isSwitching }) {
  return (
    <div className="glass-card scenario-card">
      <div className="scenario-header">
        <div className="flex-row items-center gap-2">
          <Sliders size={18} className="text-indigo" />
          <span className="scenario-card-title">Demo Workload Scenario</span>
        </div>
        <span className="badge-demo-mode">Interactive Simulator</span>
      </div>

      <p className="scenario-description">
        Switch between 6 synthetic stress scenarios to test performance telemetry, dynamic jitter, and diagnostic rules:
      </p>

      <div className="scenario-buttons-grid">
        {scenarios.map((sc) => {
          const isActive = activeScenario === sc.id;
          return (
            <button
              key={sc.id}
              className={`scenario-btn ${isActive ? "active" : ""}`}
              onClick={() => onSelect(sc.id)}
              disabled={isSwitching}
            >
              <div className="scenario-btn-top">
                <span className="scenario-btn-name">{sc.name}</span>
                {isActive && <CheckCircle2 size={16} className="text-cyan" />}
              </div>
              <span className="scenario-btn-desc">{sc.description}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
