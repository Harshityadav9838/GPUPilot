@echo off
title GPUPilot - Hackathon 1-Click Launcher
cls
echo ======================================================================
echo                GPUPilot: Universal GPU Performance Engineer
echo                      v1.0.0 Production Suite
echo ======================================================================
echo.
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not found in PATH!
    echo Please install Python 3.10+ from python.org and re-run.
    pause
    exit /b 1
)

echo [2/4] Setting up Backend Virtual Environment...
cd backend
if not exist ".venv" (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing backend dependencies...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo [3/4] Launching FastAPI Telemetry Backend (Port 8000)...
start "GPUPilot Backend Server" /min cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000"

echo [4/4] Setting up and Launching Frontend Dashboard...
cd ..\frontend
if not exist "node_modules" (
    echo Installing frontend node_modules (first run only)...
    call npm install
)

echo Starting Vite Web Server...
start "GPUPilot Frontend Server" /min cmd /c "npm run dev -- --host"

echo.
echo ======================================================================
echo    SUCCESS: GPUPilot is launching!
echo    - Dashboard: http://localhost:5173
echo    - Backend:   http://localhost:8000/docs
echo ======================================================================
echo.
echo Opening GPUPilot in your default browser in 3 seconds...
timeout /t 3 >nul
start http://localhost:5173

echo.
echo [INFO] Close the opened terminal windows to shut down GPUPilot.
pause
