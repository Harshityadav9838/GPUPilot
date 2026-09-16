import React, { useState, useEffect, useRef } from "react";
import { Header } from "./components/Header";
import { MetricsGrid } from "./components/MetricsGrid";
import { MetricsChart } from "./components/MetricsChart";
import { DiagnosticCard } from "./components/DiagnosticCard";
import { OptimizationCard } from "./components/OptimizationCard";
import { BenchmarkCard } from "./components/BenchmarkCard";
import { AgentDrawer } from "./components/AgentDrawer";
import { TuningPanel } from "./components/TuningPanel";
import { ScenarioSelector } from "./components/ScenarioSelector";
import { api } from "./services/api";
import { Play, Pause, RefreshCw, Cpu, Sliders, AlertCircle } from "lucide-react";

export function App() {
  const [gpuInfo, setGpuInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [diagnosis, setDiagnosis] = useState(null);
  const [optPlan, setOptPlan] = useState(null);
  const [benchStatus, setBenchStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [activeScenario, setActiveScenario] = useState("healthy");
  const [isPaused, setIsPaused] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [isSwitching, setIsSwitching] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("gpupilot_theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("gpupilot_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };


  const isPausedRef = useRef(isPaused);
  isPausedRef.current = isPaused;

  // Initialize data
  useEffect(() => {
    async function init() {
      try {
        const [info, m, d, plan, bStatus, scens] = await Promise.all([
          api.getGPU(),
          api.getMetrics(),
          api.getDiagnosis(),
          api.getOptimizationPlan(),
          api.getBenchmarkStatus(),
          api.getScenarios()
        ]);
        setGpuInfo(info);
        setMetrics(m);
        setDiagnosis(d);
        setOptPlan(plan);
        setBenchStatus(bStatus);
        setScenarios(scens);
        setIsOnline(true);
        setErrorMsg(null);

        setHistory([{
          ...m,
          timeStr: new Date(m.timestamp * 1000).toLocaleTimeString()
        }]);
      } catch (err) {
        console.error("Initialization failed:", err);
        setIsOnline(false);
        setErrorMsg("Failed to connect to backend server. Make sure FastAPI is running on port 8000.");
      }
    }
    init();
  }, []);

  // Polling loop
  useEffect(() => {
    const interval = setInterval(async () => {
      if (isPausedRef.current) return;

      try {
        const [m, d, plan, bStatus] = await Promise.all([
          api.getMetrics(),
          api.getDiagnosis(),
          api.getOptimizationPlan(),
          api.getBenchmarkStatus()
        ]);
        setMetrics(m);
        setDiagnosis(d);
        setOptPlan(plan);
        setBenchStatus(bStatus);
        setIsOnline(true);
        setErrorMsg(null);

        setHistory((prev) => {
          const next = [...prev, {
            ...m,
            timeStr: new Date(m.timestamp * 1000).toLocaleTimeString()
          }];
          return next.slice(-30);
        });
      } catch (err) {
        setIsOnline(false);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  // Switch Scenario handler
  const handleScenarioChange = async (scenarioId) => {
    setIsSwitching(true);
    try {
      await api.setScenario(scenarioId);
      setActiveScenario(scenarioId);
      const [newGpu, newMetrics, newDiag, newPlan] = await Promise.all([
        api.getGPU(),
        api.getMetrics(),
        api.getDiagnosis(),
        api.getOptimizationPlan()
      ]);
      setGpuInfo(newGpu);
      setMetrics(newMetrics);
      setDiagnosis(newDiag);
      setOptPlan(newPlan);
      setHistory([]);
    } catch (err) {
      console.error("Failed to switch scenario:", err);
      setErrorMsg(`Scenario switch failed: ${err.message}`);
    } finally {
      setIsSwitching(false);
    }
  };

  // Hardware vs Demo Mode Toggle
  const handleModeToggle = async () => {
    const targetMode = gpuInfo?.is_demo ? "hardware" : "demo";
    setIsSwitching(true);
    try {
      await api.switchMode(targetMode);
      const [newGpu, newMetrics, newDiag, newPlan] = await Promise.all([
        api.getGPU(),
        api.getMetrics(),
        api.getDiagnosis(),
        api.getOptimizationPlan()
      ]);
      setGpuInfo(newGpu);
      setMetrics(newMetrics);
      setDiagnosis(newDiag);
      setOptPlan(newPlan);
      setHistory([]);
    } catch (err) {
      console.error("Failed to toggle mode:", err);
      setErrorMsg(`Mode switch failed: ${err.message}`);
    } finally {
      setIsSwitching(false);
    }
  };

  const handleManualRefresh = async () => {
    try {
      const [newGpu, m, d, plan, bStatus] = await Promise.all([
        api.getGPU(),
        api.getMetrics(),
        api.getDiagnosis(),
        api.getOptimizationPlan(),
        api.getBenchmarkStatus()
      ]);
      setGpuInfo(newGpu);
      setMetrics(m);
      setDiagnosis(d);
      setOptPlan(plan);
      setBenchStatus(bStatus);
      setIsOnline(true);
      setErrorMsg(null);
    } catch (err) {
      setErrorMsg("Manual refresh failed. Check backend.");
    }
  };

  const handleTriggerBenchmark = async (testType, durationSeconds) => {
    try {
      await api.runBenchmark(testType, durationSeconds);
      const status = await api.getBenchmarkStatus();
      setBenchStatus(status);
    } catch (err) {
      console.error("Failed to run benchmark:", err);
      setErrorMsg(err.message || "Benchmark execution failed.");
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header gpuInfo={gpuInfo} isOnline={isOnline} theme={theme} onToggleTheme={toggleTheme} />

      {/* Error / Alert banner */}
      {errorMsg && (
        <div className="banner-alert">
          <div className="flex-row items-center gap-2">
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
          <button className="btn-alert-dismiss" onClick={handleManualRefresh}>
            Retry Connection
          </button>
        </div>
      )}

      {/* Controls Bar */}
      <div className="controls-bar">
        <div className="flex-row items-center gap-3">
          <span className="brand-mode-tag">
            {gpuInfo?.is_demo ? "⚡ Simulation Lab" : "⚡ Physical Hardware Telemetry"}
          </span>
          <span className="poll-badge">Polling: 2.5s</span>
        </div>

        <div className="flex-row items-center gap-2">
          <button
            className={`btn-control ${gpuInfo?.is_demo ? "mode-demo" : "mode-hw"}`}
            onClick={handleModeToggle}
            disabled={isSwitching}
            title={gpuInfo?.is_demo ? "Switch to Live Hardware" : "Switch to Demo Simulator"}
          >
            {gpuInfo?.is_demo ? <Cpu size={15} className="text-emerald" /> : <Sliders size={15} className="text-indigo" />}
            <span>{gpuInfo?.is_demo ? "Attach to Physical GPU" : "Switch to Simulator"}</span>
          </button>

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
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <main className="main-content">
        {/* Metric Cards Grid */}
        <MetricsGrid metrics={metrics} />

        {/* Charts and Diagnostic Split (Phase 8 Multi-Stream Charts) */}
        <div className="split-view">
          <div className="split-left">
            <MetricsChart history={history} theme={theme} />
          </div>
          <div className="split-right">
            <DiagnosticCard diagnosis={diagnosis} />
          </div>
        </div>

        {/* Phase 9: AI Workload Explainer Drawer */}
        <AgentDrawer />

        {/* Phase 7: GPU Benchmarking Suite Card */}
        <BenchmarkCard
          benchmarkStatus={benchStatus}
          onTriggerBenchmark={handleTriggerBenchmark}
        />

        {/* Phase 10: Autonomous Tuning Engine Card */}
        <TuningPanel />

        {/* Phase 6: Optimization Prescriptions Card */}
        <OptimizationCard plan={optPlan} />

        {/* Workload Scenario Controller */}
        <ScenarioSelector
          scenarios={scenarios}
          activeScenario={gpuInfo?.is_demo ? activeScenario : null}
          onSelect={handleScenarioChange}
          isSwitching={isSwitching}
        />
      </main>

      {/* Footer */}
      <footer className="footer-bar">
        <span>GPUPilot Production Engine • Complete 10-Phase Platform</span>
        <span>NVIDIA • AMD • Intel • Autonomous Tuning • AI Explainer</span>
      </footer>
    </div>
  );
}

export default App;
