#!/usr/bin/env bash
echo "======================================================================"
echo "               GPUPilot: Universal GPU Performance Engineer"
echo "                     v1.0.0 Production Suite"
echo "======================================================================"
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 not found! Please install Python 3.10+."
    exit 1
fi

# 2. Setup backend
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "Launching Backend on http://0.0.0.0:8000..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 3. Setup frontend
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Launching Frontend on http://0.0.0.0:5173..."
npm run dev -- --host &
FRONTEND_PID=$!

sleep 3
if which xdg-open > /dev/null; then
  xdg-open http://localhost:5173
elif which open > /dev/null; then
  open http://localhost:5173
fi

echo ""
echo "======================================================================"
echo "   GPUPilot is running!"
echo "   Dashboard: http://localhost:5173"
echo "   Press Ctrl+C to terminate both servers."
echo "======================================================================"

trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait
