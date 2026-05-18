@echo off
setlocal EnableDelayedExpansion
title AI Engineering Workspace

echo.
echo  +----------------------------------------------+
echo  ^|      AI Engineering Workspace                ^|
echo  ^|      Mission Control Launcher                ^|
echo  +----------------------------------------------+
echo.

:: ------------------------------------------------------------------
:: Check Python launcher (py)
:: ------------------------------------------------------------------
py --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Python launcher "py" not found.
    echo         Install Python 3.11+ from https://python.org
    goto :error
)
for /f "tokens=2" %%v in ('py --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python !PYVER!

:: ------------------------------------------------------------------
:: Check Node
:: ------------------------------------------------------------------
node --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Node.js not found. Install from https://nodejs.org
    goto :error
)
for /f %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo  [OK] Node !NODEVER!

:: ------------------------------------------------------------------
:: Check Ollama (optional — warn only)
:: ------------------------------------------------------------------
ollama --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [WARN] Ollama not found - install from https://ollama.ai
    echo         Set PROVIDER=anthropic if using Anthropic instead.
) else (
    echo  [OK] Ollama found
)

:: ------------------------------------------------------------------
:: Install Python dependencies
:: ------------------------------------------------------------------
echo.
echo  Installing Python dependencies...
py -m pip install -r requirements.txt -q --disable-pip-version-check
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] pip install failed
    goto :error
)
echo  [OK] Python dependencies installed

:: ------------------------------------------------------------------
:: Install frontend dependencies if node_modules is absent
:: ------------------------------------------------------------------
if not exist "dashboard\node_modules" (
    echo.
    echo  Installing frontend dependencies...
    pushd "%~dp0dashboard"
    call npm install --silent
    set NPM_RESULT=!ERRORLEVEL!
    popd
    if !NPM_RESULT! neq 0 (
        echo  [ERROR] npm install failed
        goto :error
    )
    echo  [OK] Frontend dependencies installed
) else (
    echo  [OK] Frontend dependencies present
)

:: ------------------------------------------------------------------
:: Load .env if present
:: ------------------------------------------------------------------
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "_line=%%a"
        if not "!_line:~0,1!"=="#" (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
    echo  [OK] Loaded .env
)

:: ------------------------------------------------------------------
:: Start backend first — visible titled window, stays open on error
:: ------------------------------------------------------------------
set BACKEND_PORT=8000
if defined WORKSPACE_PORT set BACKEND_PORT=!WORKSPACE_PORT!

echo.
echo  Starting backend on port %BACKEND_PORT%...
start "AI Workspace - Backend" cmd /k "py main.py --web --host 127.0.0.1 --port %BACKEND_PORT%"
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Failed to open backend window
    goto :error
)
echo  [OK] Backend window opened

:: ------------------------------------------------------------------
:: Wait for backend health endpoint to respond (up to 30 seconds).
:: Uses PowerShell Invoke-WebRequest; exits 0 on first 200 response.
:: %BACKEND_PORT% is safe here — top-level line, not inside a block.
:: ------------------------------------------------------------------
echo  Waiting for backend health check (http://127.0.0.1:%BACKEND_PORT%/api/health)...
powershell -nologo -noprofile -command "for($i=0;$i-lt30;$i++){try{if((iwr 'http://127.0.0.1:%BACKEND_PORT%/api/health' -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200){exit 0}}catch{};Start-Sleep 1};exit 1" 2>nul
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Backend did not respond within 30 seconds.
    echo         Check the backend window for startup errors.
    goto :error
)
echo  [OK] Backend healthy

:: ------------------------------------------------------------------
:: Start frontend dev server — visible titled window
:: pushd sets CWD so cmd /k gets the right directory without
:: nested-quote path issues.
:: ------------------------------------------------------------------
echo.
echo  Starting frontend dev server...
pushd "%~dp0dashboard"
start "AI Workspace - Frontend" cmd /k "npm run dev"
set FRONT_LAUNCH=!ERRORLEVEL!
popd
if !FRONT_LAUNCH! neq 0 (
    echo  [ERROR] Failed to open frontend window
    goto :error
)
echo  [OK] Frontend window opened

:: ------------------------------------------------------------------
:: Wait for Vite to initialize then open browser.
:: Vite config sets port 5173; ping -n 5 gives ~4s startup grace.
:: ------------------------------------------------------------------
echo  Waiting for Vite to initialize...
ping -n 5 127.0.0.1 >nul 2>&1

set FRONTEND_URL=http://localhost:5173
echo.
echo  [OK] Backend  : http://127.0.0.1:%BACKEND_PORT%
echo  [OK] Frontend : %FRONTEND_URL%
echo.
echo  Both services are running in their own windows.
echo  Close those windows to stop the services.
echo.

start "" "%FRONTEND_URL%"
goto :eof

:: ------------------------------------------------------------------
:error
echo.
pause
exit /b 1
