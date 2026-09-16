import React from "react";
import { Cpu, Zap, Sun, Moon } from "lucide-react";

export function Header({ gpuInfo, isOnline, theme = "dark", onToggleTheme }) {
  const isDemo = gpuInfo?.is_demo;
  const isWebEngine = gpuInfo?.provider_type === "BrowserWebEngine";

  return (
    <header className="header-container">
      <div className="header-left">
        <div className="logo-badge">
          <Zap className="logo-icon" size={24} />
        </div>
        <div>
          <div className="brand-title">
            GPUPilot
            <span className="version-pill v1">v1.0.0 • Production</span>
          </div>
          <div className="brand-subtitle">
            Universal AI GPU Performance Engineer
          </div>
        </div>
      </div>

      <div className="header-right">
        {/* Hardware / Provider Badge */}
        <div className="gpu-badge-card">
          <Cpu
            size={16}
            className={
              gpuInfo?.vendor === "NVIDIA"
                ? "text-emerald"
                : gpuInfo?.vendor === "AMD"
                ? "text-rose"
                : gpuInfo?.vendor === "Intel"
                ? "text-blue"
                : "text-cyan"
            }
          />
          <div className="gpu-badge-info">
            <span className="gpu-badge-label">
              {isWebEngine ? "Browser WebGL Detected" : "Active Accelerator"}
            </span>
            <span className="gpu-badge-value">
              {gpuInfo?.name || "Detecting Hardware..."}
            </span>
          </div>
          <span className={`vendor-tag ${gpuInfo?.vendor?.toLowerCase() || 'demo'}`}>
            {gpuInfo?.vendor || "Auto"}
          </span>
        </div>

        {/* Status Indicator */}
        <div className={`status-pill ${isWebEngine ? "webmode" : (isOnline ? (isDemo ? "demo" : "online") : "offline")}`}>
          <span className="status-dot"></span>
          <span>
            {isWebEngine
              ? "Live Web App"
              : isOnline
              ? (isDemo ? "Demo Simulation" : "Hardware Live")
              : "Connecting..."}
          </span>
        </div>

        {/* Theme Toggle Button */}
        <button
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          aria-label="Toggle dual theme"
        >
          {theme === "dark" ? (
            <>
              <Sun size={15} className="theme-icon sun" />
              <span className="theme-label">Light Mode</span>
            </>
          ) : (
            <>
              <Moon size={15} className="theme-icon moon" />
              <span className="theme-label">Dark Mode</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
