import React from "react";
import { AlertTriangle, X, RefreshCw, Cpu, CheckCircle } from "lucide-react";

export function HardwareModal({ isOpen, onClose, onRetry, gpuName, isChecking }) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-dialog glass-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="flex-row items-center gap-3">
            <div className="modal-icon-badge">
              <AlertTriangle size={22} className="text-amber" />
            </div>
            <div>
              <h3 className="modal-title">Cannot Attach to Physical GPU Sensors</h3>
              <p className="modal-subtitle">Local hardware telemetry daemon not detected</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Detected Chip Banner */}
          <div className="modal-chip-banner">
            <Cpu size={16} className="text-cyan" />
            <span>
              Detected Hardware: <strong>{gpuName || "Graphics Accelerator"}</strong>
            </span>
            <span className="modal-tag-pill">WebGL Layer</span>
          </div>

          {/* Root Cause Explanation */}
          <div className="modal-section">
            <h4 className="modal-section-title">🔍 Why is this happening?</h4>
            <div className="modal-reasons-list">
              <div className="modal-reason-item">
                <span className="reason-bullet">1.</span>
                <div>
                  <strong>Browser Security Restrictions:</strong>
                  <p>
                    Modern web browsers (Chrome, Edge, Safari) strictly isolate websites from directly reading internal motherboard temperature diodes, fan RPM, or PCIe power rails without a local companion app.
                  </p>
                </div>
              </div>
              <div className="modal-reason-item">
                <span className="reason-bullet">2.</span>
                <div>
                  <strong>Local Daemon Not Running:</strong>
                  <p>
                    To stream real physical hardware telemetry, GPUPilot requires its local Python NVML/WMI daemon running on <code>http://localhost:8000</code> on this computer.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* How to Connect */}
          <div className="modal-section">
            <h4 className="modal-section-title">⚡ How to stream real hardware telemetry:</h4>
            <div className="modal-steps-box">
              <div className="modal-step">
                <span className="step-number">1</span>
                <span>Download or clone this project onto this computer:</span>
              </div>
              <div className="code-snippet-line">
                <code>git clone https://github.com/Harshityadav9838/GPUPilot.git</code>
              </div>

              <div className="modal-step">
                <span className="step-number">2</span>
                <span>Double-click the 1-click launcher in the project folder:</span>
              </div>
              <div className="code-snippet-line">
                <code>start.bat</code> <span className="text-muted">(or <code>./start.sh</code> on Mac/Linux)</span>
              </div>

              <div className="modal-step">
                <span className="step-number">3</span>
                <span>Open your local dashboard (bypasses browser mixed-content blocks):</span>
              </div>
              <div className="code-snippet-line flex-row items-center justify-between">
                <code>http://localhost:5173</code>
                <a href="http://localhost:5173" target="_blank" rel="noreferrer" className="modal-launch-link">
                  Open Local Dashboard ↗
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button className="btn-modal-secondary" onClick={onClose}>
            Continue in Simulation Lab
          </button>
          <button className="btn-modal-primary" onClick={onRetry} disabled={isChecking}>
            <RefreshCw size={14} className={isChecking ? "spin" : ""} />
            <span>{isChecking ? "Checking Port 8000..." : "Retry Local Connection"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
