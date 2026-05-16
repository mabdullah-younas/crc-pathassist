@echo off
setlocal EnableDelayedExpansion
title CRC-PathAssist Launcher

:: ============================================================
::  CRC-PathAssist — One-click launcher
::  Starts the FastAPI backend + React frontend simultaneously.
::  Run this from the project root directory.
:: ============================================================

echo.
echo  =========================================================
echo    CRC-PathAssist ^| Gemma 4 Good Hackathon
echo    Privacy-preserving AI pathology assistant
echo  =========================================================
echo.

:: ── 0. Confirm we're in the right directory ───────────────────────────────────
if not exist "backend\api.py" (
    echo [ERROR] Please run this script from the project root directory.
    echo         Expected to find: backend\api.py
    pause
    exit /b 1
)

:: ── 1. Check Python ───────────────────────────────────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11 or 3.12 from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo         Found Python %PYVER%

:: Verify Python version is stable (3.10 to 3.13) and not experimental (3.14+)
python -c "import sys; sys.exit(0 if sys.version_info[:2] in [(3, 10), (3, 11), (3, 12), (3, 13)] else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [CRITICAL ERROR] Python %PYVER% is an experimental release.
    echo scikit-learn and other backend packages will fail to install.
    echo Please install a stable version (Python 3.11 or 3.12 recommended).
    echo.
    pause
    exit /b 1
)

:: ── 2. Check Node.js ─────────────────────────────────────────────────────────
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo        Found Node.js %NODEVER%

:: ── 3. Check Ollama ──────────────────────────────────────────────────────────
echo [3/5] Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not found in PATH.
    echo           Download from https://ollama.ai/ and run: ollama pull gemma4:e4b
    echo           The backend will serve mock data until Ollama is available.
    echo.
) else (
    for /f %%v in ('ollama --version 2^>^&1') do set OLLAMAVER=%%v
    echo        Found Ollama %OLLAMAVER%
)

:: ── 4. Set up Python virtual environment ─────────────────────────────────────
echo [4/5] Setting up Python environment...

if not exist "env\Scripts\activate.bat" (
    echo        Creating virtual environment...
    python -m venv env
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)
echo        Virtual environment ready.

:: Activate venv for this script's session (to check pip, etc.)
call env\Scripts\activate.bat

:: Install / update backend dependencies
echo        Installing backend dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed. Check requirements.txt and your Python version.
    pause
    exit /b 1
)
echo        Backend dependencies OK.

:: ── 4b. Copy .env if missing ──────────────────────────────────────────────────
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        echo        Creating backend\.env from .env.example...
        copy "backend\.env.example" "backend\.env" >nul
    )
)

:: ── 5. Set up Node / frontend ─────────────────────────────────────────────────
echo [5/5] Setting up frontend...
if not exist "frontend\node_modules" (
    echo        Running npm install ^(first-time setup, may take a minute^)...
    cd frontend
    npm install --silent
    if errorlevel 1 (
        echo [ERROR] npm install failed. Ensure Node.js 18+ is installed.
        cd ..
        pause
        exit /b 1
    )
    cd ..
)
echo        Frontend dependencies OK.

:: ── Launch servers ────────────────────────────────────────────────────────────
echo.
echo  Starting servers...
echo  ─────────────────────────────────────────────────────────
echo   Backend API  →  http://localhost:8000
echo   Frontend App →  http://localhost:3000
echo   API Docs     →  http://localhost:8000/docs
echo  ─────────────────────────────────────────────────────────
echo.
echo  [TIP] Both server windows will open separately.
echo        Close them (or press Ctrl+C inside each) to stop.
echo.

:: Start backend in a new titled window
start "CRC-PathAssist — Backend API (port 8000)" cmd /k ^
    "cd /d "%~dp0" && call env\Scripts\activate.bat && cd backend && python -m uvicorn api:app --reload --port 8000"

:: Small delay so backend gets a head start
timeout /t 2 /nobreak >nul

:: Start frontend in a new titled window
start "CRC-PathAssist — Frontend (port 3000)" cmd /k ^
    "cd /d "%~dp0frontend" && npm run dev"

:: Open browser after servers have time to start
timeout /t 4 /nobreak >nul
echo  Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo  =========================================================
echo   Both servers are running. This window can be closed.
echo   To stop: close the Backend and Frontend server windows.
echo  =========================================================
echo.
pause
endlocal
