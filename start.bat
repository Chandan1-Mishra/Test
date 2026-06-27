@echo off
:: ─────────────────────────────────────────────────────────────
:: SOLARIS — One-shot startup script (Windows)
:: Usage: Double-click start.bat  OR  run from terminal
:: ─────────────────────────────────────────────────────────────

echo.
echo  ======================================
echo    SOLARIS - Architecture Intelligence
echo  ======================================
echo.

:: ── 1. Check Python ───────────────────────────────────────────
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)

:: ── 2. Check Node ─────────────────────────────────────────────
node --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)

:: ── 3. Check .env ─────────────────────────────────────────────
IF NOT EXIST "backend\.env" (
    echo [ERROR] backend\.env not found.
    echo   Copy backend\.env.example to backend\.env and add your ANTHROPIC_API_KEY
    pause & exit /b 1
)

:: ── 4. Backend venv + deps ────────────────────────────────────
echo [1/4] Setting up Python environment...
cd backend
IF NOT EXIST ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo [OK] Backend dependencies ready
cd ..

:: ── 5. Start backend in new window ───────────────────────────
echo [2/4] Starting backend...
start "SOLARIS Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: ── 6. Frontend deps ─────────────────────────────────────────
echo [3/4] Installing frontend dependencies...
cd frontend
call npm install --silent
echo [OK] Frontend dependencies ready

:: ── 7. Start frontend in new window ──────────────────────────
echo [4/4] Starting frontend...
start "SOLARIS Frontend" cmd /k "cd frontend && npm run dev"
cd ..

echo.
echo  ======================================
echo    SOLARIS is ready!
echo    Backend:   http://localhost:8000
echo    Frontend:  http://localhost:3000
echo  ======================================
echo.
pause
