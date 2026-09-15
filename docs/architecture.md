# GPUPilot Architecture

GPUPilot is designed around a decoupled, vendor-agnostic provider/adapter architecture. The core diagnostics and UI never depend on proprietary GPU APIs directly.

```
                  +-----------------------------------+
                  |   GPUPilot React/Vite Frontend    |
                  +-----------------+-----------------+
                                    | REST Polling (2.5s)
                                    v
                  +-----------------------------------+
                  |          FastAPI Backend          |
                  +-----------------+-----------------+
                                    |
                                    v
                            [ GPU Detector ]
                                    |
            +---------------+-------+-------+---------------+
            |               |               |               |
            v               v               v               v
    +---------------+---------------+---------------+---------------+
    | NVIDIAProvider|  AMDProvider  | IntelProvider |  DemoProvider |
    |   (NVML)      |   (AMD SMI)   | (Intel Level0)| (6 Scenarios) |
    +---------------+---------------+---------------+---------------+
            |               |               |               |
            +---------------+-------+-------+---------------+
                                    |
                                    v
                         [ Standardized GPUMetrics ]
                                    |
                        +-----------+-----------+
                        |                       |
                        v                       v
            [ Diagnostic Engine ]    [ Benchmark & Optimizer ]
```

## Standardized GPU Metrics Schema

Every provider guarantees returning the exact same normalized structure:
- `vendor` (str): e.g. "NVIDIA", "AMD", "Intel", "Demo"
- `name` (str): Model name, e.g. "RTX 3050"
- `gpu_utilization` (float, %): 0 to 100
- `memory_used` (float, GB)
- `memory_total` (float, GB)
- `memory_utilization` (float, %)
- `temperature` (float, ?C)
- `power_usage` (float, W)
- `power_limit` (float, W)
- `fan_speed` (float, %)
- `gpu_clock` (float, MHz)
- `memory_clock` (float, MHz)
- `cpu_utilization` (float, %)
- `latency` (float, ms)
- `throughput` (float, req/s)

If a vendor or driver does not provide a particular metric, GPUPilot strictly outputs `null` rather than fabricating numbers.

## Phase 1 Implementation

In Phase 1, hardware stubs safely probe for driver availability without crashing or raising unhandled exceptions. If no hardware monitoring library is available, GPUPilot gracefully falls back to `DemoProvider`, offering 6 dynamic workloads:
1. Healthy
2. Compute bottleneck
3. Memory bottleneck
4. CPU bottleneck
5. Thermal problem
6. VRAM pressure
