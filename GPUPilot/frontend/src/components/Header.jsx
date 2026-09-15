import React from "react";
import { Cpu, Zap } from "lucide-react";

export function Header({ gpuInfo, isOnline }) {
  const isDemo = gpuInfo?.is_demo;

  return (
    <header className="header-container">
      <div className="header-left">
        <div className="logo-badge">
          <Zap className="logo-icon" size={24} />
        </div>
        <div>
          <div className="brand-title">
            GPUPilot
            <span className="version-pill">v0.1.0 ? Phase 1</span>
          </div>
          <div className="brand-subtitle">
            Universal AI GPU Performance Engineer
          </div>
        </div>
      </div>

      <div className="header-right">
        {/* Hardware / Provider Badge */}
        <div className="gpu-badge-card">
          <Cpu size={16} className="text-cyan" />
          <div className="gpu-badge-info">
            <span className="gpu-badge-label">Active Accelerator</span>
            <span className="gpu-badge-value">
              {gpuInfo?.name || "Detecting Hardware..."}
            </span>
          </div>
          <span className={`vendor-tag ${gpuInfo?.vendor?.toLowerCase() || 'demo'}`}>
            {gpuInfo?.vendor || "Auto"}
          </span>
        </div>

        {/* Status Indicator */}
        <div className={`status-pill ${isOnline ? "online" : "offline"}`}>
          <span className="status-dot"></span>
          <span>{isOnline ? (isDemo ? "Demo Simulation" : "Hardware Live") : "Connecting..."}</span>
        </div>
      </div>
    </header>
  );
}
