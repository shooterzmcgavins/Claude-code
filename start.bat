@echo off
setlocal EnableDelayedExpansion
title AI Engineering Workspace

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║      AI Engineering Workspace                ║
echo  ║      Mission Control Launcher                ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER%

:: ── Check Node ───────────────────────────────────────────────────────────────
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARN] Node.js not found - frontend will use pre-built files only
    set SKIP_BUILD=1
) else (
    for /f %%v in ('node --version 2^>^&1') do set NODEVER=%%v
    echo  [OK] Node %NODEVER%
)

:: ── Check Ollama ──────────────────────────────────────────────────────────────
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARN] Ollama not found - install from https://ollama.ai
    echo         You can still use PROVIDER=anthropic if you have an API key.
) else (
    echo  [OK] Ollama found
)

:: ── Install Python dependencies ───────────────────────────────────────────────
echo.
echo  Installing Python dependencies...
pip install -r requirements.txt -q --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [ERROR] pip install failed
    pause
    exit /b 1
)
echo  [OK] Python dependencies installed

:: ── Build frontend ────────────────────────────────────────────────────────────
if not defined SKIP_BUILD (
    if not exist "dashboard\dist\index.html" (
        echo.
        echo  Building frontend...
        cd dashboard
        call npm install --silent
        call npm run build
        set BUILD_RESULT=%errorlevel%
        cd ..
        if %BUILD_RESULT% neq 0 (
            echo  [WARN] Frontend build failed - running in API-only mode
        ) else (
            echo  [OK] Frontend built
        )
    ) else (
        echo  [OK] Frontend already built
    )
)

:: ── Load .env if present ─────────────────────────────────────────────────────
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
    echo  [OK] Loaded .env
)

:: ── Start server ──────────────────────────────────────────────────────────────
set HOST=127.0.0.1
set PORT=8000
if not "%WORKSPACE_PORT%"=="" set PORT=%WORKSPACE_PORT%

echo.
echo  Starting Mission Control on http://%HOST%:%PORT%
echo  Press Ctrl+C to stop.
echo.

:: Open browser after short delay (use ping for delay — works in both cmd and Git Bash)
start "" /b cmd /c "ping -n 3 127.0.0.1 >nul 2>&1 & start http://%HOST%:%PORT%"

python main.py --web --host %HOST% --port %PORT%
