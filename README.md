# ⚡ GPUPilot — Universal AI GPU Performance Engineer

> **A real-time telemetry, bottleneck detection, optimization prescription, and benchmarking platform for heterogeneous GPU workloads.**  
> Built for NVIDIA, AMD, and Intel architectures with automatic hardware discovery, deterministic rule-based diagnostics, and interactive AI assistance.

---

## 🌟 Key Highlights & Innovations

1. **Universal Multi-Vendor Telemetry (Zero Config)**:
   - **NVIDIA**: Low-overhead hardware telemetry via official NVML (`pynvml`) capturing core utilization, VRAM allocation, temperature, fan speeds, and power draw.
   - **AMD**: Driver-level telemetry via `amdsmi` with safe cross-platform sensor fallbacks.
   - **Intel**: DXGI Performance Counters & WMI integration for Intel UHD, Iris Xe, and Arc accelerators.
   - **Simulation Lab**: 6 dynamic stress workload profiles for evaluating edge-case bottlenecks (Thermal runaway, VRAM exhaustion, CPU starvation) without risking hardware.

2. **Autonomous Bottleneck Detection Engine**:
   - 6 prioritized deterministic diagnostic rules evaluating silicon and system constraints with confidence scoring.
   - Diagnoses **Thermal Throttling**, **VRAM OOM Hazard**, **Compute Saturation**, **CPU Starvation**, **Memory Bandwidth Choke**, and **VRAM Pressure**.

3. **Optimization Recommendation Engine**:
   - Direct engineering prescriptions tailored to the active bottleneck.
   - Copyable code snippets for **Automatic Mixed Precision (AMP FP16)**, **TorchDynamo compilation (`torch.compile`)**, **Gradient Checkpointing**, **BitsAndBytes INT8 Quantization**, and **DALI GPU Decoding**.

4. **Integrated GPU Benchmarking Suite**:
   - Standardized Compute (GEMM), Memory Bandwidth, and Mixed Stress benchmark routines.
   - Asynchronous background telemetry delta tracking: baseline vs. peak temperature, thermal rise (`+°C`), clock stability, and standardized **0–1000 Composite Score**.

5. **AI Agent / LLM Workload Explainer**:
   - Natural language assistant explaining *why* constraints occur (e.g. laptop thermal envelope vs. desktop, CPU draw-call bottlenecks, 4GB VRAM survival strategies).

6. **Safe Autonomous Tuning Engine**:
   - **Power Saver**, **Balanced**, and **Maximum Performance** operational profiles with dry-run verification and instant rollback.

---

## 🚀 Quick Start Guide

### 🌐 Option A: Test Live Online (Zero Installation — Instant for Judges)
You do not need to download or install anything to test GPUPilot! Open the live web app directly:

👉 **[Launch Live Web Dashboard (gpu-pilot.vercel.app)](https://gpu-pilot.vercel.app/)**

*Automatically detects your browser's graphics chip (NVIDIA, Intel, AMD, or Apple Silicon) and lets you test all 10 phases, failure scenarios, benchmarks, tuning profiles, and dual theme directly in your browser.*

---

### 💻 Option B: Run on Physical GPU Hardware (Local Machine)

If you want GPUPilot to connect to your computer's **real physical GPU hardware sensors** (reading live diode temperatures, fan RPM, and PCIe wattage via NVML / WMI):

#### 1. Download the Project
* **Option 1**: Click the green **`<> Code`** button at the top right of this GitHub page → Click **`Download ZIP`**, then extract the ZIP folder.
* **Option 2** (via Git):
  ```bash
  git clone https://github.com/Harshityadav9838/GPUPilot.git
  cd GPUPilot
  ```

#### 2. Launch with 1-Click
* **Windows (Recommended)**:  
  Open the extracted folder in Windows File Explorer and double-click:
  ```cmd
  start.bat
  ```
  *(Or run `.\start.bat` in your terminal)*.
  *This automatically creates the Python virtual environment, installs backend dependencies, starts FastAPI and Vite, and opens your browser directly to `http://localhost:5173`!*

* **macOS / Linux**:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

---

## 🛠️ Manual Installation (Alternative)

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv .venv

# Windows:
.\.venv\Scriptsctivate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
API Documentation will be live at: `http://localhost:8000/docs`

### 2. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev -- --host
```
Dashboard will be live at: `http://localhost:5173`

---

## 🧪 Automated Testing Suite

GPUPilot features extensive automated test coverage across all 10 phases. Run the test suite:
```bash
cd backend
pytest tests/ -v
```
**Result: 42 passed in ~14 seconds** ✅

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              React + Vite Dark Dashboard                │
│    (Telemetry Grid • Multi-Stream Charts • AI Drawer)   │
└────────────────────────────┬────────────────────────────┘
                             │ REST / Polling (2.5s)
┌────────────────────────────▼────────────────────────────┐
│                  FastAPI Backend Engine                 │
├────────────────────────────┬────────────────────────────┤
│   Provider / Adapter Layer │   Diagnostic & Bench Suite │
│  ┌──────────────────────┐  │  ┌──────────────────────┐  │
│  │   NVIDIAProvider     │  │  │ Bottleneck Detector  │  │
│  │   (NVML pynvml)      │  │  │ (6-Rule Priority)    │  │
│  ├──────────────────────┤  │  ├──────────────────────┤  │
│  │   AMDProvider        │  │  │ Optimizer Prescriber │  │
│  │   (amdsmi safe)      │  │  │ (Actionable Code)    │  │
│  ├──────────────────────┤  │  ├──────────────────────┤  │
│  │   IntelProvider      │  │  │ Benchmarking Engine  │  │
│  │   (WMI / DXGI)       │  │  │ (Deltas & Scoring)   │  │
│  ├──────────────────────┤  │  ├──────────────────────┤  │
│  │   DemoProvider       │  │  │ Autonomous Tuner     │  │
│  │   (6 Stress Profiles)│  │  │ (Safe Envelopes)     │  │
│  └──────────────────────┘  │  └──────────────────────┘  │
└────────────────────────────┴────────────────────────────┘
```

---

## 📦 Project Structure

```
GPUPilot/
├── start.bat                   # 1-Click launcher for Windows
├── start.sh                    # 1-Click launcher for Linux/macOS
├── README.md                   # Project documentation
├── backend/
│   ├── api/routes.py           # REST endpoints (Telemetry, Diagnose, Bench, Agent, Tuner)
│   ├── gpu/
│   │   ├── base.py             # Abstract GPUProvider base class
│   │   ├── nvidia.py           # NVIDIA NVML provider
│   │   ├── amd.py              # AMD ROCm/smi provider
│   │   ├── intel.py            # Intel DXGI/WMI provider
│   │   ├── demo.py             # 6-scenario simulator with dynamic jitter
│   │   ├── detector.py         # Hardware autodetection engine
│   │   ├── diagnostics.py      # Deterministic bottleneck rules engine
│   │   ├── optimizer.py        # Remediation prescriptions with code
│   │   ├── benchmark.py        # Compute/Memory stress test engine
│   │   ├── agent.py            # AI Workload Explainer layer
│   │   └── tuner.py            # Autonomous tuning profile manager
│   ├── models/schemas.py       # Pydantic data schemas
│   ├── requirements.txt        # Backend dependencies
│   └── tests/                  # 41 comprehensive pytest test cases
└── frontend/
    ├── src/
    │   ├── components/         # Glassmorphic React UI components
    │   ├── services/api.js     # Unified API client
    │   ├── App.jsx             # Master application coordinator
    │   └── index.css           # Modern dark cybernetic styling
    ├── package.json
    └── vite.config.js
```

---

## 📄 License
MIT License — Free to use, adapt, and distribute for Hackathons, Research, and Production deployments.
