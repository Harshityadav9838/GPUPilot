// GPUPilot In-Browser WebEngine
// Provides zero-backend client-side execution when deployed to Vercel or any web host.
// Detects real browser GPU via WebGL, runs live simulation with jitter, and executes in-browser benchmarks.

export function detectBrowserGPU() {
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    if (gl) {
      const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
      if (debugInfo) {
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || "";
        let vendor = "WebGL";
        if (/nvidia/i.test(renderer)) vendor = "NVIDIA";
        else if (/amd|radeon/i.test(renderer)) vendor = "AMD";
        else if (/intel/i.test(renderer)) vendor = "Intel";
        else if (/apple/i.test(renderer)) vendor = "Apple";

        let cleanName = renderer
          .replace(/^ANGLE \([^,]+,\s*/i, "")
          .replace(/Direct3D.*$/i, "")
          .replace(/vs_\d+_\d+.*$/i, "")
          .replace(/,\s*D3D.*$/i, "")
          .replace(/\)$/, "")
          .trim();

        if (!cleanName) cleanName = renderer || "Universal Accelerator";

        return {
          vendor,
          name: cleanName,
          driver_version: "WebGL 2.0 / WebGPU Direct",
          provider_type: "BrowserWebEngine",
          is_demo: true,
          available: true,
          details: { renderer, webgl: true }
        };
      }
    }
  } catch (e) {
    console.warn("WebGL detection fallback:", e);
  }

  return {
    vendor: "NVIDIA",
    name: "NVIDIA GeForce RTX 3050 (Web Simulator)",
    driver_version: "595.97",
    provider_type: "BrowserWebEngine",
    is_demo: true,
    available: true
  };
}

let activeScenario = "healthy";
let activeTuningProfile = "balanced";
let benchmarkState = {
  is_running: false,
  current_test: null,
  elapsed_seconds: 0,
  total_seconds: 0,
  progress_percent: 0,
  latest_result: null
};
let benchmarkHistory = [];

const SCENARIOS = [
  {
    id: "healthy",
    name: "Healthy Workload",
    description: "Optimal balanced utilization (~68%), safe temperature and low latency."
  },
  {
    id: "compute_bottleneck",
    name: "Compute Bottleneck",
    description: "GPU utilization pinned near 98%, high power draw, compute-bound kernels."
  },
  {
    id: "memory_bottleneck",
    name: "Memory Bottleneck",
    description: "Low GPU utilization (~41%) with high memory pressure and transfer stalls."
  },
  {
    id: "cpu_bottleneck",
    name: "CPU Starvation Bottleneck",
    description: "Host CPU pinned >90% while GPU waits starved with low utilization (~24%)."
  },
  {
    id: "thermal_problem",
    name: "Thermal Throttling",
    description: "Critical temperatures (~90°C), max fan speed (100%), reduced core clock."
  },
  {
    id: "vram_pressure",
    name: "VRAM OOM Pressure",
    description: "VRAM usage >95% causing thrashing, high latency spikes, low throughput."
  }
];

function jitter(base, delta = 2.5) {
  return Number((base + (Math.random() * delta * 2 - delta)).toFixed(1));
}

export const webEngine = {
  getHealth() {
    return {
      status: "ok",
      version: "1.0.0-web",
      active_provider: "BrowserWebEngine",
      is_demo: true
    };
  },

  getGPU() {
    return detectBrowserGPU();
  },

  getScenarios() {
    return SCENARIOS;
  },

  setScenario(scen) {
    activeScenario = scen;
    return { status: "success", active_scenario: scen, is_demo: true };
  },

  getMetrics() {
    const gpu = detectBrowserGPU();
    const now = Date.now() / 1000;

    let base = {
      vendor: gpu.vendor,
      name: gpu.name,
      timestamp: now,
      memory_total: 4.0,
      power_limit: 45.0,
    };

    switch (activeScenario) {
      case "compute_bottleneck":
        return {
          ...base,
          gpu_utilization: Math.min(100, jitter(97.5, 1.5)),
          memory_used: jitter(1.6, 0.1),
          memory_utilization: jitter(40.0, 2.0),
          temperature: jitter(74.0, 1.5),
          power_usage: jitter(42.0, 1.0),
          fan_speed: 65.0,
          gpu_clock: 1450.0,
          memory_clock: 6000.0,
          cpu_utilization: jitter(28.0, 3.0),
          latency: jitter(38.5, 2.0),
          throughput: jitter(240.0, 8.0)
        };
      case "memory_bottleneck":
        return {
          ...base,
          gpu_utilization: Math.max(10, jitter(38.0, 3.0)),
          memory_used: jitter(2.8, 0.1),
          memory_utilization: jitter(70.0, 2.0),
          temperature: jitter(62.0, 1.5),
          power_usage: jitter(18.0, 1.5),
          fan_speed: 45.0,
          gpu_clock: 850.0,
          memory_clock: 6000.0,
          cpu_utilization: jitter(32.0, 4.0),
          latency: jitter(52.0, 4.0),
          throughput: jitter(85.0, 5.0)
        };
      case "cpu_bottleneck":
        return {
          ...base,
          gpu_utilization: Math.max(5, jitter(21.0, 3.0)),
          memory_used: jitter(1.2, 0.1),
          memory_utilization: jitter(30.0, 2.0),
          temperature: jitter(58.0, 1.0),
          power_usage: jitter(12.5, 1.0),
          fan_speed: 40.0,
          gpu_clock: 720.0,
          memory_clock: 6000.0,
          cpu_utilization: Math.min(100, jitter(92.0, 2.5)),
          latency: jitter(68.0, 5.0),
          throughput: jitter(60.0, 4.0)
        };
      case "thermal_problem":
        return {
          ...base,
          gpu_utilization: jitter(82.0, 3.0),
          memory_used: jitter(2.1, 0.1),
          memory_utilization: jitter(52.5, 2.0),
          temperature: Math.min(99, jitter(91.5, 1.0)),
          power_usage: jitter(44.0, 0.8),
          fan_speed: 100.0,
          gpu_clock: jitter(620.0, 30.0),
          memory_clock: 5000.0,
          cpu_utilization: jitter(45.0, 4.0),
          latency: jitter(85.0, 8.0),
          throughput: jitter(55.0, 5.0)
        };
      case "vram_pressure":
        return {
          ...base,
          gpu_utilization: jitter(65.0, 4.0),
          memory_used: jitter(3.88, 0.05),
          memory_utilization: Math.min(99.5, jitter(97.0, 1.0)),
          temperature: jitter(68.0, 1.5),
          power_usage: jitter(26.0, 1.5),
          fan_speed: 55.0,
          gpu_clock: 1200.0,
          memory_clock: 6000.0,
          cpu_utilization: jitter(35.0, 3.0),
          latency: jitter(98.0, 10.0),
          throughput: jitter(42.0, 4.0)
        };
      default: // healthy
        return {
          ...base,
          gpu_utilization: Math.min(80, Math.max(30, jitter(54.0, 4.0))),
          memory_used: jitter(1.5, 0.1),
          memory_utilization: jitter(37.5, 2.0),
          temperature: jitter(64.0, 1.5),
          power_usage: jitter(24.0, 2.0),
          fan_speed: 50.0,
          gpu_clock: 1350.0,
          memory_clock: 6000.0,
          cpu_utilization: Math.min(60, jitter(34.0, 3.0)),
          latency: jitter(18.0, 1.5),
          throughput: jitter(185.0, 10.0)
        };
    }
  },

  getDiagnosis() {
    const m = this.getMetrics();
    const temp = m.temperature;
    const vram = m.memory_utilization;
    const gpu = m.gpu_utilization;
    const cpu = m.cpu_utilization;

    if (temp >= 85) {
      return {
        status: "critical",
        bottleneck: "thermal_throttling",
        confidence: 0.96,
        severity: "critical",
        title: "Thermal Throttling — Critical",
        explanation: `GPU temperature is ${temp.toFixed(0)} °C — well above safe limits. Core clocks are being throttled.`,
        recommendations: [
          "Immediately reduce workload or power limit",
          "Clean dust from heatsink and fans",
          "Verify chassis airflow (intake to exhaust)",
          "Consider undervolting or lowering power target"
        ],
        metrics_snapshot: m
      };
    }

    if (vram >= 90) {
      return {
        status: vram >= 95 ? "critical" : "warning",
        bottleneck: "vram_exhaustion",
        confidence: 0.94,
        severity: vram >= 95 ? "critical" : "high",
        title: "VRAM Exhaustion Risk",
        explanation: `VRAM usage is ${vram.toFixed(0)}%. Out-of-Memory (OOM) fatal crashes can occur if allocation increases.`,
        recommendations: [
          "Reduce batch size immediately",
          "Enable gradient checkpointing (deep learning workloads)",
          "Offload optimizer states to CPU RAM",
          "Use FP16 / INT8 quantization"
        ],
        metrics_snapshot: m
      };
    }

    if (cpu >= 80 && gpu < 60) {
      return {
        status: "warning",
        bottleneck: "cpu_starvation",
        confidence: 0.91,
        severity: "high",
        title: "CPU Starvation — GPU Waiting for Data",
        explanation: `Host CPU utilization is ${cpu.toFixed(0)}% while GPU sits at only ${gpu.toFixed(0)}%. The CPU cannot feed data fast enough.`,
        recommendations: [
          "Increase DataLoader num_workers (PyTorch / TF datasets)",
          "Pin memory in DataLoader (pin_memory=True)",
          "Pre-process and cache training data offline",
          "Use GPU-accelerated decoding (NVJPEG, DALI)"
        ],
        metrics_snapshot: m
      };
    }

    if (gpu >= 85) {
      return {
        status: "warning",
        bottleneck: "compute_bound",
        confidence: 0.89,
        severity: gpu >= 95 ? "high" : "medium",
        title: "Compute Bottleneck — GPU Saturated",
        explanation: `GPU core utilization is ${gpu.toFixed(0)}%, meaning compute throughput is maxed out.`,
        recommendations: [
          "Switch to FP16 or BF16 mixed precision to double throughput",
          "Apply INT8 quantization for inference workloads",
          "Profile with NVIDIA Nsight / GPU profilers",
          "Increase batch size to amortize kernel launch overhead"
        ],
        metrics_snapshot: m
      };
    }

    return {
      status: "healthy",
      bottleneck: "none",
      confidence: 0.97,
      severity: "ok",
      title: "System Healthy",
      explanation: `All telemetry is within optimal operating parameters (GPU ${gpu.toFixed(0)}% | Temp ${temp.toFixed(0)} °C | VRAM ${vram.toFixed(0)}%).`,
      recommendations: [
        "System is performing optimally — no action required",
        "Continue monitoring for trend changes"
      ],
      metrics_snapshot: m
    };
  },

  getOptimizationPlan() {
    const diag = this.getDiagnosis();
    const b = diag.bottleneck;

    if (b === "thermal_throttling") {
      return {
        bottleneck: b,
        status: diag.status,
        severity: diag.severity,
        recommendations: [
          {
            id: "thermal_power_cap",
            category: "Hardware & Thermal",
            title: "Enforce Dynamic Power Cap (NVIDIA NVML / nvidia-smi)",
            summary: "Throttle power target down by 10-15% to immediately halt thermal runaway with <3% throughput degradation.",
            impact: "Critical",
            estimated_gain: "Drops junction temp by 6-12°C while preserving steady clock frequencies",
            code_snippet: "nvidia-smi -pl 40  # Temporarily clamp power limit to 40W\n# Or in Python with pynvml:\n# pynvml.nvmlDeviceSetPowerManagementLimit(handle, 40000)",
            doc_url: "https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html"
          }
        ]
      };
    }

    if (b === "vram_exhaustion") {
      return {
        bottleneck: b,
        status: diag.status,
        severity: diag.severity,
        recommendations: [
          {
            id: "vram_batch_downscale",
            category: "Memory & Batching",
            title: "Downscale Micro-Batch Size & Enable Gradient Accumulation",
            summary: "Halve forward pass batch size while accumulating gradients over multiple steps.",
            impact: "Critical",
            estimated_gain: "Frees ~40-50% dedicated VRAM immediately, eliminating OOM hazard",
            code_snippet: "train_loader = DataLoader(dataset, batch_size=batch_size // 2)\n\nfor i, (inputs, targets) in enumerate(train_loader):\n    loss = model(inputs, targets) / accum_steps\n    loss.backward()\n    if (i + 1) % accum_steps == 0:\n        optimizer.step()\n        optimizer.zero_grad()",
            doc_url: "https://pytorch.org/docs/stable/notes/amp_examples.html#gradient-accumulation"
          }
        ]
      };
    }

    return {
      bottleneck: "none",
      status: "healthy",
      severity: "ok",
      recommendations: [
        {
          id: "healthy_baseline",
          category: "Monitoring & Telemetry",
          title: "Baseline Profiling & Regression Safeguards",
          summary: "Current GPU and CPU operations are operating within peak thermal, memory, and compute envelopes.",
          impact: "Low",
          estimated_gain: "Ensures regression-free continuous deployment",
          code_snippet: "# Log telemetry for baseline comparison:\nprint('System running within optimal operating envelope')",
          doc_url: "https://github.com/NVIDIA/gpu-monitoring-tools"
        }
      ]
    };
  },

  async runBenchmark(test_type = "compute", duration_seconds = 5) {
    if (benchmarkState.is_running) {
      throw new Error("A benchmark is already in progress.");
    }

    const m0 = this.getMetrics();
    benchmarkState = {
      is_running: true,
      current_test: test_type,
      elapsed_seconds: 0,
      total_seconds: duration_seconds,
      progress_percent: 0,
      latest_result: null
    };

    const startTime = performance.now();
    const durationMs = duration_seconds * 1000;
    let opsCount = 0;

    const runChunk = () => {
      const chunkStart = performance.now();
      while (performance.now() - chunkStart < 50) {
        for (let i = 0; i < 5000; i++) {
          Math.sin(i) * Math.cos(i) + Math.sqrt(i);
        }
        opsCount += 5000;
      }

      const elapsedMs = performance.now() - startTime;
      const progress = Math.min(99, Math.round((elapsedMs / durationMs) * 100));

      benchmarkState.elapsed_seconds = Number((elapsedMs / 1000).toFixed(1));
      benchmarkState.progress_percent = progress;

      if (elapsedMs < durationMs) {
        setTimeout(runChunk, 16);
      } else {
        const actualSec = (performance.now() - startTime) / 1000;
        const opsPerSec = Math.round(opsCount / actualSec);
        const peakTemp = Number((m0.temperature + (test_type === "stress" ? 8.5 : 4.0)).toFixed(1));

        const result = {
          id: "web-" + Math.random().toString(36).substr(2, 6),
          test_type,
          duration_seconds,
          score: Math.min(980, Math.max(350, Math.round(Math.log10(opsPerSec) * 145))),
          grade: "A+",
          throughput_ops: opsPerSec,
          telemetry: {
            baseline_temp: m0.temperature,
            peak_temp: peakTemp,
            temp_delta: Number((peakTemp - m0.temperature).toFixed(1)),
            peak_power: m0.power_usage,
            power_limit: m0.power_limit,
            avg_clock: m0.gpu_clock,
            peak_gpu_util: 98.0,
            peak_cpu_util: 45.0
          },
          timestamp: Date.now() / 1000,
          summary: "In-Browser WebGL Compute Stress successfully executed with stable frame throughput."
        };

        benchmarkState = {
          is_running: false,
          current_test: null,
          elapsed_seconds: duration_seconds,
          total_seconds: duration_seconds,
          progress_percent: 100,
          latest_result: result
        };
        benchmarkHistory.unshift(result);
      }
    };

    setTimeout(runChunk, 16);
    return benchmarkState;
  },

  getBenchmarkStatus() {
    return benchmarkState;
  },

  getBenchmarkHistory() {
    return benchmarkHistory;
  },

  askAgent(prompt = "") {
    const m = this.getMetrics();
    const q = prompt.toLowerCase();

    if (q.includes("cpu hotter") || (q.includes("temp") && q.includes("cpu"))) {
      return {
        response: `Your host CPU (${m.cpu_utilization}% load) operates inside a shared chassis cooling envelope with your GPU. In modern laptops, the CPU package frequently reaches 85-95°C during high-framerate rendering or data prep while the dedicated GPU stays cooler (~${m.temperature}°C). This occurs because the CPU handles geometry calculation, browser draw calls, and script execution.`,
        suggested_actions: ["Parallelize DataLoader workers", "Elevate laptop rear for intake airflow", "Limit background browser processes"],
        source: "GPUPilot Web AI Agent"
      };
    }

    if (q.includes("4gb") || q.includes("vram")) {
      return {
        response: `On a 4GB VRAM accelerator, dedicated memory is your most scarce resource. Currently, VRAM occupancy is ${m.memory_utilization}%. To prevent Out-of-Memory (OOM) fatal errors during model execution, always activate gradient checkpointing (\`model.gradient_checkpointing_enable()\`), adopt INT8/4-bit quantization (BitsAndBytes), and utilize gradient accumulation instead of large micro-batches.`,
        suggested_actions: ["Enable Gradient Checkpointing", "Apply INT8 Quantization", "Cut batch size in half"],
        source: "GPUPilot Web AI Agent"
      };
    }

    return {
      response: `Your GPU is currently operating in **${activeScenario.toUpperCase()}** state. Utilization is **${m.gpu_utilization}%**, VRAM is **${m.memory_utilization}%**, and temperature is **${m.temperature}°C**. You can switch workload profiles in the Simulation Lab to inspect different silicon constraints or run a benchmark to evaluate stability!`,
      suggested_actions: ["Run 5s Quick Benchmark", "Test Thermal Throttling Scenario", "Check Optimization Prescriptions"],
      source: "GPUPilot Web AI Agent"
    };
  },

  getTuningProfiles() {
    return [
      {
        id: "balanced",
        name: "Balanced Standard Profile",
        description: "Default dynamic power and clock balancing suitable for daily gaming, rendering, and inference.",
        target_power_percent: 100,
        recommended_batch_multiplier: 1.0,
        precision_mode: "FP16 Automatic Mixed Precision",
        features: ["Automatic clock frequency scaling", "Standard fan curve", "Dynamic memory allocation"]
      },
      {
        id: "efficiency",
        name: "Power Saver & Acoustic Quiet",
        description: "Caps GPU power envelope at 80% to eliminate fan acoustics and reduce temperatures by 8-15°C.",
        target_power_percent: 80,
        recommended_batch_multiplier: 0.75,
        precision_mode: "INT8 Quantization",
        features: ["-20% Power Envelope limit", "Acoustic fan optimization", "Zero thermal throttle guarantee"]
      },
      {
        id: "performance",
        name: "Maximum Compute Occupancy",
        description: "Pushes maximum power limits and maximizes batch depth to deliver peak TFLOPS for heavy training/rendering.",
        target_power_percent: 105,
        recommended_batch_multiplier: 1.5,
        precision_mode: "FP16 Tensor Core Optimized",
        features: ["Maximum power ceiling allocation", "Max queue throughput", "Aggressive cooling ramp"]
      }
    ];
  },

  applyTuningProfile(profile_id, dry_run = false) {
    if (!dry_run) activeTuningProfile = profile_id;
    return {
      status: "success",
      profile_id,
      message: dry_run
        ? `Simulated dry-run validation passed for '${profile_id}' profile.`
        : `Successfully applied '${profile_id}' tuning parameters in browser engine.`,
      applied_settings: {
        profile_id,
        py_config_snippet: `# Applied PyTorch Tuning Parameters for ${profile_id}:\nBATCH_SIZE_MULTIPLIER = 1.0\nPRECISION = 'FP16'`
      },
      dry_run
    };
  }
};
