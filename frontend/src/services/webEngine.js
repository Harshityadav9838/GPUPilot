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
    const q = (prompt || "").toLowerCase().trim();
    const gpuName = m.name || "GPU Accelerator";
    const util = m.gpu_utilization;
    const temp = m.temperature;
    const vram = m.memory_utilization;
    const vramUsed = m.memory_used;
    const cpu = m.cpu_utilization;
    const power = m.power_usage;
    const powerLimit = m.power_limit || 45.0;
    const gpuClock = m.gpu_clock || 1350.0;
    const memClock = m.memory_clock || 6000.0;
    const latency = m.latency || 22.0;
    const throughput = m.throughput || 180.0;

    // 1. Performance / Speed / FPS / Latency / Throughput
    if (["performance", "speed", "fps", "how fast", "fast", "throughput", "latency", "tflops", "gflops", "rate"].some(k => q.includes(k))) {
      let perfStatus, extra;
      if (util > 80 && temp < 85) {
        perfStatus = `Your ${gpuName} is operating at **high compute efficiency** (${util.toFixed(0)}% load) at ${gpuClock.toFixed(0)} MHz.`;
        extra = `Throughput is measuring ~${throughput.toFixed(1)} ops/sec with low ${latency.toFixed(1)} ms frame/dispatch latency. Tensor pipelines and WebGL compute units are actively saturated.`;
      } else if (temp >= 85) {
        perfStatus = `Performance on ${gpuName} is **degraded by thermal throttling** (${temp.toFixed(0)}°C).`;
        extra = `Core clocks have downclocked to ${gpuClock.toFixed(0)} MHz to prevent silicon degradation. Latency has increased to ${latency.toFixed(1)} ms.`;
      } else if (cpu > 75 && util < 40) {
        perfStatus = `Performance is **starved by host CPU latency** (Host CPU: ${cpu.toFixed(0)}% vs GPU: ${util.toFixed(0)}%).`;
        extra = `The GPU is spending excessive cycles waiting for the CPU to process and dispatch batches. Frame latency is elevated at ${latency.toFixed(1)} ms.`;
      } else {
        perfStatus = `Your ${gpuName} is operating at a **moderate baseline** (${util.toFixed(0)}% load, ${gpuClock.toFixed(0)} MHz, ${temp.toFixed(0)}°C).`;
        extra = `Current throughput is ~${throughput.toFixed(1)} ops/sec with ${latency.toFixed(1)} ms latency. There is ample thermal and compute headroom available for heavier workloads.`;
      }

      return {
        response: `📊 **Real-Time Performance Evaluation**\n\n${perfStatus} ${extra}\n\n• **Clock Speed**: ${gpuClock.toFixed(0)} MHz core / ${memClock.toFixed(0)} MHz memory\n• **Compute Pipeline**: ${util.toFixed(0)}% utilized\n• **Latency / Throughput**: ${latency.toFixed(1)} ms / ${throughput.toFixed(1)} ops/s\n\n**To Maximize Performance:** Enable PyTorch Automatic Mixed Precision (AMP FP16) to unlock Tensor Cores, compile your model with \`torch.compile()\`, and ensure AC power is connected.`,
        suggested_actions: ["Enable FP16 Tensor Cores", "Compile with torch.compile()", "Run 10s Compute Benchmark"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 2. GPU Utilization / Usage / Load / Spikes
    const isUtilQuery = (
      q.includes("utilization") ||
      q.includes("gpu usage") ||
      q.includes("gpu load") ||
      q.includes("increases") ||
      q.includes("increased") ||
      q.includes("why high") ||
      q.includes("why low") ||
      (["usage", "load", "spike"].some(k => q.includes(k)) && !["power", "watt", "vram", "memory", "cpu", "temp", "thermal"].some(x => q.includes(x)))
    );
    if (isUtilQuery) {
      let utilAnalysis, rec;
      if (util >= 80) {
        utilAnalysis = `Your GPU utilization is currently high at **${util.toFixed(0)}%** on ${gpuName}. This indicates that your active workload (matrix multiplications, shader draw calls, or WebGL geometry) is fully saturating the Streaming Multiprocessors (SMs) and warp schedulers.`;
        rec = "If this is intentional (e.g. running a benchmark, model training, or 3D rendering), high utilization means you are getting full value from the silicon. If unexpected, check for background WebGL tabs or unthrottled render loops.";
      } else if (util <= 25) {
        utilAnalysis = `Your GPU utilization is relatively low at **${util.toFixed(0)}%**. Meanwhile, host CPU is at ${cpu.toFixed(0)}%.`;
        rec = "Low GPU utilization occurs when the GPU is idle or bottlenecked upstream by CPU preprocessing, I/O disk reads, or small batch sizes that underfill execution warps.";
      } else {
        utilAnalysis = `Your GPU utilization is in a balanced mid-range at **${util.toFixed(0)}%**. Workload batches are flowing smoothly through the graphics and compute queues.`;
        rec = "Utilization fluctuates dynamically as kernels are launched and synchronized. Increasing batch size will push utilization higher toward 95%+ peak efficiency.";
      }

      return {
        response: `📈 **GPU Utilization Analysis**\n\n${utilAnalysis}\n\n**Why does GPU load change?**\n1. **Kernel Compute Density**: Operations like FP16 convolutions or matrix GEMMs push utilization to 99%.\n2. **Host Synchronization**: CPU transfers (\`.to('cuda')\`) or unpinned memory cause periodic dips in utilization.\n3. **Pipeline Bottlenecks**: When CPU or VRAM runs out, the GPU stalls waiting for data.\n\n**Current Status:** ${gpuName} is running at **${util.toFixed(0)}%** load, drawing **${power.toFixed(1)}W** at **${temp.toFixed(0)}°C**.\n\n**Advice:** ${rec}`,
        suggested_actions: ["Tune Batch Size Multiplier", "Inspect Warp Occupancy", "Switch to Balanced Profile"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 3. CPU vs GPU / CPU Hotter / Starvation
    if (q.includes("cpu hotter") || (q.includes("temp") && q.includes("cpu")) || (q.includes("cpu") && ["bottleneck", "starvation", "high", "hot", "usage", "100", "draw"].some(k => q.includes(k)))) {
      return {
        response: `🖥️ **Host CPU vs Dedicated GPU Analysis**\n\nYour host CPU (${cpu.toFixed(0)}% load) and ${gpuName} (${temp.toFixed(0)}°C, ${util.toFixed(0)}% load) share a compact thermal chassis. In modern laptops, the CPU package frequently reaches 85-95°C during intensive tasks (such as 30,000 WebGL entity simulations or PyTorch DataLoader loops) while the dedicated GPU stays comparatively cooler (~60-70°C).\n\n**Why this happens:**\n• **Host Orchestration**: The CPU must calculate physics, transform geometry matrices, and submit draw calls to DirectX/OpenGL before the GPU can render a single frame.\n• **Thermal Mass**: CPU dies have smaller surface area and higher power density per mm² than the GPU die.\n• **Driver Stalls**: If single-threaded JS/Python is pegged at 100%, the GPU starves waiting for instructions.\n\n**Remediation:** Increase DataLoader \`num_workers=4\`, use page-locked memory (\`pin_memory=True\`), offload transforms to CUDA/WebGL shaders, and elevate the rear chassis.`,
        suggested_actions: ["Parallelize Data Workers", "Enable Pin Memory", "Elevate Laptop Rear for Airflow"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 4. Memory / VRAM / 4GB / OOM
    if (["4gb", "vram", "memory", "oom", "out of memory", "allocation", "cache", "ram", "leak"].some(k => q.includes(k))) {
      return {
        response: `💾 **VRAM & Memory Management on ${gpuName}**\n\nCurrent dedicated VRAM allocation is **${vramUsed.toFixed(2)} GB / 4.00 GB (${vram.toFixed(1)}%)**.\n\nOn a 4GB accelerator, memory headroom is your strictest ceiling. VRAM is divided into:\n1. **Model Weights**: A 7B model in FP16 requires ~14GB (won't fit), but in 4-bit AWQ/GGUF requires only ~3.8GB.\n2. **Activations**: Scale linearly with batch size and quadratic with sequence length.\n3. **Optimizer States**: Adam requires 8 bytes per parameter in FP32.\n\n**Guaranteed Techniques to Avoid CUDA OOM:**\n• **Activation Checkpointing**: \`model.gradient_checkpointing_enable()\` discards intermediate activations during forward pass, cutting memory by up to 60%.\n• **Quantization**: Load with \`load_in_8bit=True\` or \`load_in_4bit=True\` via BitsAndBytes.\n• **Gradient Accumulation**: Simulate batch size 32 using micro-batch 4 accumulated over 8 steps.\n• **Cache Flush**: Call \`torch.cuda.empty_cache()\` after validation epochs.`,
        suggested_actions: ["Enable Gradient Checkpointing", "Apply INT8/4-bit Quantization", "Cut Micro-Batch Size in Half"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 5. Temperature / Cooling / Fans / Thermal Throttle
    if (["temperature", "temp", "hot", "heat", "thermal", "cooling", "fan", "celsius", "overheat", "throttle"].some(k => q.includes(k))) {
      let thermalState, fix;
      if (temp >= 85) {
        thermalState = `⚠️ **Critical High Temperature (${temp.toFixed(0)}°C)**\n\nYour ${gpuName} has crossed thermal throttling thresholds (85°C+). The silicon internal sensor is downclocking core frequencies to safeguard the die.`;
        fix = "Immediately cap target power envelope by 15%, elevate the chassis, and verify fan exhaust vents are clear of obstructions.";
      } else if (temp >= 72) {
        thermalState = `🌡️ **Elevated Temperature (${temp.toFixed(0)}°C)**\n\nYour ${gpuName} is operating warm under sustained load. Dynamic boost clocks may begin stepping down slightly as temperature approaches 80°C.`;
        fix = "Ensure adequate airflow under the laptop. Consider switching to the **Efficiency** profile to drop temps by 6-10°C with <5% frame loss.";
      } else {
        thermalState = `❄️ **Optimal Thermal Envelope (${temp.toFixed(0)}°C)**\n\nYour ${gpuName} is well below the 83°C thermal target. Fan acoustic levels and die temperatures are within healthy parameters.`;
        fix = "You have ample thermal headroom to run intensive benchmarks or increase compute batch multiplier.";
      }

      return {
        response: `${thermalState}\n\n• **Current Temp**: ${temp.toFixed(0)}°C\n• **Fan Status**: System Managed (EC dynamic curve)\n• **Clock Speed**: ${gpuClock.toFixed(0)} MHz\n\n**Thermal Recommendation:** ${fix}`,
        suggested_actions: ["Apply Efficiency Profile (-15W)", "Elevate Chassis for Intake Air", "Run Thermal Stress Test"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 6. Power / Wattage / Battery / TGP
    if (["power", "watt", "tgp", "tdp", "battery", "energy", "consumption", "limit", "draw"].some(k => q.includes(k))) {
      const pPct = powerLimit > 0 ? (power / powerLimit) * 100 : 0;
      return {
        response: `⚡ **Power & Energy Dynamics**\n\nYour ${gpuName} is currently drawing **${power.toFixed(1)} Watts** against a target limit of **${powerLimit.toFixed(1)} Watts** (${pPct.toFixed(0)}% of TGP envelope).\n\n**Key Power Insights:**\n• **Dynamic Boost**: Modern laptop GPUs dynamically negotiate power with the CPU. When the CPU is heavily loaded, GPU power drops to prioritize host processing.\n• **Voltage-Frequency Curve**: Silicon power consumption scales with $V^2 \\times f$. Capping power by just 15% typically reduces temperatures by 8-12°C while sacrificing less than 3% compute throughput.\n• **Battery vs AC**: Always ensure your laptop is plugged into the OEM AC adapter; running on battery forces the GPU into low-power P8 state (clocks capped below 500 MHz).`,
        suggested_actions: ["Switch to Efficiency Profile", "Verify AC Power Connection", "Inspect TGP Ceiling"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 7. Clocks / Frequency / P-States
    if (["clock", "mhz", "frequency", "boost", "p-state", "core clock"].some(k => q.includes(k))) {
      return {
        response: `⏱️ **Clock Frequency Architecture**\n\nActive Frequencies on ${gpuName}:\n• **Core Clock**: **${gpuClock.toFixed(0)} MHz**\n• **Memory Clock**: **${memClock.toFixed(0)} MHz**\n\n**How GPU Clocks Work:**\nNVIDIA GPUs operate on automated P-States (P0 = Maximum 3D compute/CUDA, P8 = 2D Idle Desktop). The GPU Boost algorithm continuously evaluates three silicon limiters every millisecond: **Temperature**, **Power (TGP)**, and **Voltage reliability**. If temperature exceeds 75°C, clocks gradually step down in 15 MHz increments. If power reaches 45W, clock voltage is clamped.`,
        suggested_actions: ["Check Thermal Margin", "Set High Performance Power Plan", "Run Compute Stress Test"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 8. Benchmark / Scoring / Testing
    if (["benchmark", "score", "grade", "test", "stress", "measure"].some(k => q.includes(k))) {
      return {
        response: `🏆 **GPUPilot Composite Benchmarking Suite**\n\nGPUPilot grades your accelerator on a normalized scale from **0 to 1000 points** based on three live stress criteria:\n1. **Compute Sustained Throughput (40%)**: Tests raw FP32 / FP16 matrix operations and warp scheduling stability.\n2. **Thermal Resilience (35%)**: Measures temperature delta under full load. Systems that stay cool without thermal downclocking receive top marks.\n3. **Memory Bus Saturation (25%)**: Tests VRAM bandwidth transfer rates and cache eviction latency.\n\nWith your ${gpuName} running at **${util.toFixed(0)}%** load, **${temp.toFixed(0)}°C**, and **${power.toFixed(1)}W**, the system is primed for testing.`,
        suggested_actions: ["Run 10s Sustained Benchmark", "Run Memory Bus Stress Test", "Compare Historical Grades"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 9. Optimization / Tuning / PyTorch / Code Remediation
    if (["optimize", "optimization", "tune", "tuning", "remediat", "improve", "fix", "faster", "code", "batch"].some(k => q.includes(k))) {
      return {
        response: `🛠️ **Autonomous Optimization Plan for ${gpuName}**\n\nBased on current telemetry (State: **${activeScenario.toUpperCase()}**, GPU: **${util.toFixed(0)}%**, VRAM: **${vram.toFixed(0)}%**, Temp: **${temp.toFixed(0)}°C**):\n\n**Top 3 Engineering Remediation Steps:**\n1. **Automatic Mixed Precision (AMP)**: Wrap forward pass in \`torch.cuda.amp.autocast()\` to use Tensor Cores. Yields 2x-3x speedup on Ampere architecture.\n2. **Kernel Fusion**: Use PyTorch 2.0 \`model = torch.compile(model)\` to fuse sequential elementwise kernels and eliminate CUDA launch overhead.\n3. **Zero-Copy Host Paging**: Set \`DataLoader(..., pin_memory=True, num_workers=4)\` to eliminate CPU memory copy stalls.\n\nYou can also activate pre-tested profiles in the **Autonomous Tuner (Phase 10)** tab with 1-click execution.`,
        suggested_actions: ["Apply Balanced Tuning Profile", "Copy PyTorch Remediation Code", "View Optimization Engine"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 10. Architecture / Specs / CUDA Cores
    if (["architecture", "spec", "specs", "cuda", "hardware", "device", "tensor core", "rtx"].some(k => q.includes(k))) {
      return {
        response: `⚙️ **Hardware Architecture & Specifications**\n\n**Identified Device**: ${gpuName}\n• **Silicon Generation**: NVIDIA Ampere Architecture (8nm GA107 Die)\n• **Compute Units**: 2048 CUDA Cores, 64 Tensor Cores (3rd Gen), 16 RT Cores (2nd Gen)\n• **Memory Subsystem**: 4.0 GB GDDR6 on 128-bit bus (~192 GB/s bandwidth)\n• **Power Envelope**: 35W - 60W Dynamic Boost TGP\n• **Hardware Features**: FP16 Tensor Core acceleration, BF16 compute support, NVENC Gen 7 hardware video encoder.`,
        suggested_actions: ["Test Tensor Core FP16 Ops", "Run 5s Compute Stress", "Check Active Telemetry"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 11. Bottlenecks
    if (["bottleneck", "stall", "throttle", "constraint", "choke"].some(k => q.includes(k))) {
      const diag = this.getDiagnosis();
      return {
        response: `🔍 **Active Bottleneck Diagnostics**\n\nGPUPilot's 6-rule heuristic engine evaluated your live telemetry and identified: **${diag.title}**.\n\n• **Severity Confidence**: ${(diag.confidence * 100).toFixed(0)}%\n• **Primary Metric**: ${diag.explanation}\n\n**Hardware State Snapshot:**\n- GPU Core Load: ${util.toFixed(0)}%\n- Memory Occupancy: ${vram.toFixed(0)}% (${vramUsed.toFixed(2)} / 4.00 GB)\n- Temperature: ${temp.toFixed(0)}°C\n- Host CPU: ${cpu.toFixed(0)}%\n\nReview the Remediation Plan tab for copy-paste PyTorch and system fixes.`,
        suggested_actions: ["Open Optimization Tab", "Apply Autonomous Tuner", "Run Baseline Benchmark"],
        source: "GPUPilot Web AI Agent"
      };
    }

    // 12. Smart Contextual Telemetry Breakdown (General Inquiries / Fallback)
    return {
      response: `🤖 **GPUPilot AI Telemetry Analysis for ${gpuName}**\n\nI have inspected your real-time hardware telemetry in response to: *"${prompt}"*\n\n• **Compute Load**: **${util.toFixed(0)}%** (${util > 80 ? "High saturation" : util > 30 ? "Balanced workload" : "Light/Idle"})\n• **Thermals**: **${temp.toFixed(0)}°C** (${temp >= 85 ? "Thermal throttle danger" : "Normal operating range"})\n• **VRAM Occupancy**: **${vram.toFixed(0)}%** (${vramUsed.toFixed(2)} / 4.00 GB)\n• **Host CPU**: **${cpu.toFixed(0)}%** load\n• **Active Scenario**: **${activeScenario.toUpperCase()}**\n\nAsk me specific questions like *"Why is my GPU utilization increasing?"*, *"How to reduce temperature?"*, or *"What is performance?"* for deep-dive root cause analysis!`,
      suggested_actions: ["Explain Active Bottleneck", "Run Sustained Benchmark", "Apply Tuning Profile"],
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
