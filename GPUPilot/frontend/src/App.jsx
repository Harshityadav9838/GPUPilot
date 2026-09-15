import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { MetricsGrid } from "./components/MetricsGrid";
import { MetricsChart } from "./components/MetricsChart";
import { ScenarioSelector } from "./components/ScenarioSelector";
import { DiagnosticCard } from "./components/DiagnosticCard";
import { api } from "./services/api";
import { RefreshCw, Play, Pause, Activity } from "lucide-react";

export default function App() {
  const [gpuInfo, setGpuInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [activeScenario, setActiveScenario] = useState("healthy");
  const [diagnosis, setDiagnosis] = useState(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSwitching, setIsSwitching] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // 1. Initial Load: Fetch static GPU info & scenario definitions
  useEffect(() => {
    async function init() {
      try {
        const [gpuData, scenariosData, diagData] = await Promise.all([
          api.getGPU(),
          api.getScenarios(),
          api.getDiagnosis(),
        ]);
        setGpuInfo(gpuData);
        setScenarios(scenariosData);
        setDiagnosis(diagData);
        if (gpuData.details?.scenario) {
          setActiveScenario(gpuData.details.scenario);
        }
        setIsOnline(true);
      } catch (err) {
        console.error("Initial load error:", err);
        setErrorMsg("Failed to connect to GPUPilot Backend on http://localhost:8000");
        setIsOnline(false);
      }
    }
    init();
  }, []);

  // 2. Real-Time Telemetry Poller (Every 2.5 seconds)
  useEffect(() => {
    if (isPaused) return;

    const fetchTelemetry = async () => {
      try {
        const [m, d] = await Promise.all([
          api.getMetrics(),
          api.getDiagnosis()
        ]);
        setMetrics(m);
        setDiagnosis(d);
        setIsOnline(true);
        setErrorMsg(null);

        const timeStr = new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });

        setHistory((prev) => {
          const next = [...prev, { ...m, timeStr }];
          return next.slice(-25);
        });
      } catch (err) {
        console.warn("Telemetry polling warning:", err);
        setIsOnline(false);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2500);
    return () => clearInterval(interval);
  }, [isPaused, activeScenario]);

  // Scenario Switch Handler
  const handleScenarioChange = async (scenarioId) => {
    setIsSwitching(true);
    try {
      await api.setScenario(scenarioId);
      setActiveScenario(scenarioId);
      const [newMetrics, newDiag] = await Promise.all([
        api.getMetrics(),
        api.getDiagnosis()
      ]);
      setMetrics(newMetrics);
      setDiagnosis(newDiag);
    } catch (err) {
      console.error("Failed to set scenario:", err);
    } finally {
      setIsSwitching(false);
    }
  };

  const handleManualRefresh = async () => {
    try {
      const [m, d] = await Promise.all([api.getMetrics(), api.getDiagnosis()]);
      setMetrics(m);
      setDiagnosis(d);
      setIsOnline(true);
    } catch (err) {
      setErrorMsg("Manual refresh failed. Check backend.");
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        gpuInfo={gpuInfo}
        isOnline={isOnline}
        activeScenario={activeScenario}
      />

      {/* Error alert bar */}
      {errorMsg && (
        <div className="error-banner">
          <span>{errorMsg}</span>
          <button className="btn-sm" onClick={handleManualRefresh}>
            Retry Connection
          </button>
        </div>
      )}

      {/* Control Strip */}
      <div className="controls-bar">
        <div className="flex-row items-center gap-2">
          <Activity size={18} className="text-cyan animate-pulse" />
          <span className="text-sm font-semibold">Live Telemetry Stream</span>
          <span className="poll-badge">Polling: 2.5s</span>
        </div>

        <div className="flex-row items-center gap-2">
          <button
            className={`btn-control ${isPaused ? "active-paused" : ""}`}
            onClick={() => setIsPaused(!isPaused)}
            title={isPaused ? "Resume real-time stream" : "Pause stream"}
          >
            {isPaused ? <Play size={15} /> : <Pause size={15} />}
            <span>{isPaused ? "Resume" : "Pause"}</span>
          </button>

          <button
            className="btn-control"
            onClick={handleManualRefresh}
            title="Force immediate refresh"
          >
            <RefreshCw size={15} />
            <span>Refresh Metrics</span>
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <main className="main-content">
        {/* Metric Cards Grid */}
        <MetricsGrid metrics={metrics} />

        {/* Charts and Diagnostic Split */}
        <div className="split-view">
          <div className="split-left">
            <MetricsChart history={history} />
          </div>
          <div className="split-right">
            <DiagnosticCard diagnosis={diagnosis} />
          </div>
        </div>

        {/* Demo Scenario Controller */}
        {gpuInfo?.is_demo && (
          <ScenarioSelector
            scenarios={scenarios}
            activeScenario={activeScenario}
            onSelect={handleScenarioChange}
            isSwitching={isSwitching}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="footer-bar">
        <span>GPUPilot Engine ? Universal Vendor Hardware Abstraction</span>
        <span>Supports NVIDIA, AMD, Intel & Demo Mode</span>
      </footer>
    </div>
  );
}
