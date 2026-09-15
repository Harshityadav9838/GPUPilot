import React, { useState } from "react";
import { Play, Flame, Activity, Award, CheckCircle, Clock, Zap } from "lucide-react";

export function BenchmarkCard({ benchmarkStatus, onTriggerBenchmark }) {
  const [selectedType, setSelectedType] = useState("compute");
  const [selectedDuration, setSelectedDuration] = useState(5);

  const isRunning = benchmarkStatus?.is_running;
  const result = benchmarkStatus?.latest_result;

  const getGradeColor = (grade) => {
    switch (grade) {
      case "A+": return "grade-aplus";
      case "A": return "grade-a";
      case "B": return "grade-b";
      case "C": return "grade-c";
      default: return "grade-throttled";
    }
  };

  return (
    <div className="glass-card benchmark-card">
      <div className="bench-header">
        <div className="flex-row items-center gap-2">
          <div className="bench-icon-badge">
            <Flame size={18} className="text-amber" />
          </div>
          <div>
            <div className="bench-title">GPU Performance Benchmarking Suite</div>
            <div className="bench-subtitle">
              Run standardized stress routines to establish before/after performance baselines
            </div>
          </div>
        </div>

        {isRunning && (
          <div className="bench-running-pill">
            <span className="bench-pulse-dot"></span>
            <span>Running {benchmarkStatus.current_test?.toUpperCase()} ({benchmarkStatus.progress_percent}%)</span>
          </div>
        )}
      </div>

      {/* Progress Track when running */}
      {isRunning && (
        <div className="bench-progress-container">
          <div
            className="bench-progress-fill"
            style={{ width: `${benchmarkStatus.progress_percent}%` }}
          />
        </div>
      )}

      {/* Controls / Options */}
      <div className="bench-controls-row">
        <div className="bench-test-selector">
          <button
            className={`bench-type-btn ${selectedType === "compute" ? "active" : ""}`}
            onClick={() => setSelectedType("compute")}
            disabled={isRunning}
          >
            <Zap size={14} />
            <span>Compute (FP32/GEMM)</span>
          </button>
          <button
            className={`bench-type-btn ${selectedType === "memory" ? "active" : ""}`}
            onClick={() => setSelectedType("memory")}
            disabled={isRunning}
          >
            <Activity size={14} />
            <span>Memory Bandwidth</span>
          </button>
          <button
            className={`bench-type-btn ${selectedType === "stress" ? "active" : ""}`}
            onClick={() => setSelectedType("stress")}
            disabled={isRunning}
          >
            <Flame size={14} />
            <span>Full Stress Loop</span>
          </button>
        </div>

        <div className="flex-row items-center gap-2">
          <select
            className="bench-duration-select"
            value={selectedDuration}
            onChange={(e) => setSelectedDuration(Number(e.target.value))}
            disabled={isRunning}
          >
            <option value={5}>5s Quick Test</option>
            <option value={10}>10s Sustained</option>
            <option value={15}>15s Thermal Soak</option>
          </select>

          <button
            className="btn-start-bench"
            onClick={() => onTriggerBenchmark(selectedType, selectedDuration)}
            disabled={isRunning}
          >
            <Play size={14} />
            <span>{isRunning ? "Running..." : "Start Benchmark"}</span>
          </button>
        </div>
      </div>

      {/* Latest Result Card */}
      {result && (
        <div className="bench-result-box">
          <div className="bench-result-top">
            <div className="flex-row items-center gap-3">
              <div className={`grade-badge ${getGradeColor(result.grade)}`}>
                {result.grade}
              </div>
              <div>
                <div className="bench-score-label">GPUPilot Composite Score</div>
                <div className="bench-score-value">{result.score} <span className="score-pts">/ 1000 pts</span></div>
              </div>
            </div>
            <div className="bench-meta">
              <span>{result.test_type.toUpperCase()} • {result.duration_seconds}s</span>
              <span>{new Date(result.timestamp * 1000).toLocaleTimeString()}</span>
            </div>
          </div>

          <p className="bench-summary-text">{result.summary}</p>

          {/* Telemetry Delta Comparison */}
          <div className="bench-delta-grid">
            <div className="delta-stat">
              <span className="delta-label">Baseline Temp</span>
              <span className="delta-val">{result.telemetry.baseline_temp ?? "?"} °C</span>
            </div>
            <div className="delta-stat">
              <span className="delta-label">Peak Temp</span>
              <span className="delta-val text-amber">{result.telemetry.peak_temp ?? "?"} °C</span>
            </div>
            <div className="delta-stat">
              <span className="delta-label">Thermal Delta</span>
              <span className="delta-val text-rose">+{result.telemetry.temp_delta ?? 0} °C</span>
            </div>
            <div className="delta-stat">
              <span className="delta-label">Peak Power</span>
              <span className="delta-val">{result.telemetry.peak_power ?? "?"} W</span>
            </div>
            <div className="delta-stat">
              <span className="delta-label">Peak GPU Load</span>
              <span className="delta-val text-cyan">{result.telemetry.peak_gpu_util ?? "?"} %</span>
            </div>
            <div className="delta-stat">
              <span className="delta-label">Peak CPU Load</span>
              <span className="delta-val">{result.telemetry.peak_cpu_util ?? "?"} %</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
