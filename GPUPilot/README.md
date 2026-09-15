# GPUPilot ??
### Universal AI GPU Performance Engineer

GPUPilot is an AI-powered GPU performance engineering platform supporting **NVIDIA**, **AMD**, **Intel**, and an interactive **Demo Mode** using a unified provider architecture.

---

## ?? Features (Phase 1)
- **Universal Provider Architecture**: Decoupled `GPUProvider` base class ensuring the core engine and UI are completely vendor-agnostic.
- **Safe Fallback & Hardware Detection**: Auto-detects available GPU drivers (NVIDIA NVML, AMD SMI, Intel) and falls back safely to Demo Mode without crashing.
- **6 Realistic Demo Scenarios**:
  1. *Healthy Workload* (~68% util, safe temp, low latency)
  2. *Compute Bottleneck* (~98% util, high power)
  3. *Memory Bottleneck* (low GPU util, high memory pressure)
  4. *CPU Bottleneck* (>90% CPU, GPU starvation)
  5. *Thermal Throttling* (~90?C, max fan speed, throttled clocks)
  6. *VRAM Pressure* (>95% VRAM allocation, high latency)
- **Real-Time Telemetry Stream**: Polling every 2.5 seconds with live Recharts rolling trend lines.
- **Autonomous Diagnosis Engine Preview**: Instant deterministic rule analysis and optimization suggestions matching the workload state.
- **Modern AI Infrastructure Dashboard**: Dark glassmorphic interface with crisp typography and responsive layout.

---

## ?? Project Structure

```
GPUPilot/
??? backend/
?   ??? main.py              # FastAPI server entrypoint
?   ??? config.py            # Pydantic Settings & CORS
?   ??? requirements.txt     # Python dependencies
?   ??? api/
?   ?   ??? __init__.py
?   ?   ??? routes.py        # REST endpoints (/health, /gpu, /metrics, /demo/scenario)
?   ??? gpu/
?   ?   ??? base.py          # Abstract GPUProvider interface
?   ?   ??? detector.py      # Autodetection priority & fallback logic
?   ?   ??? demo.py          # DemoProvider with 6 dynamic scenarios
?   ?   ??? nvidia.py        # NVIDIA NVML provider stub (Phase 2)
?   ?   ??? amd.py           # AMD SMI provider stub (Phase 3)
?   ?   ??? intel.py         # Intel LevelZero provider stub (Phase 4)
?   ??? engine/              # Bottleneck and optimizer modules
?   ??? models/
?   ?   ??? schemas.py       # Pydantic standardized schemas
?   ??? tests/
?       ??? test_phase1.py   # Pytest automated test suite
??? frontend/
?   ??? src/
?   ?   ??? components/      # Glassmorphic UI components & charts
?   ?   ??? services/api.js  # Backend fetch client
?   ?   ??? App.jsx          # State, polling loop, scenario handler
?   ?   ??? main.jsx         # Vite root entry
?   ?   ??? index.css        # Modern dark cyber theme
?   ??? package.json
?   ??? vite.config.js
??? docs/
?   ??? architecture.md      # Architecture documentation
??? .env.example
??? .gitignore
??? README.md
```

---

## ?? Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

---

### 1. Running the Backend

Open a terminal in the `GPUPilot/backend` directory:

```bash
cd backend

# Create a virtual environment (if not already created)
python -m venv .venv

# Activate the virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server with live reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will start at: `http://localhost:8000`
- Swagger Interactive Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- GPU Telemetry: `http://localhost:8000/metrics`

To run backend tests:
```bash
pytest tests/test_phase1.py
```

---

### 2. Running the Frontend

Open a second terminal in the `GPUPilot/frontend` directory:

```bash
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Vite dev server
npm run dev
```

The frontend dashboard will be live at: `http://localhost:5173`

---

## ?? Testing Scenarios in Demo Mode

1. Open `http://localhost:5173` in your browser.
2. In the **Demo Workload Scenario** section at the bottom, click any scenario (e.g. *Thermal Throttling*).
3. Observe the metric cards immediately adapt:
   - Temperature rises to ~90?C (colored red).
   - Fan speed hits 100%.
   - The Autonomous Diagnosis Engine flags `THERMAL THROTTLING` with 96% confidence and prescribes cooling/power optimizations.
