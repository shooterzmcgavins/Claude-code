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
:: Check Python
:: ------------------------------------------------------------------
python --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Python not found. Install Python 3.11+ from https://python.org
    goto :error
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python !PYVER!

:: ------------------------------------------------------------------
:: Check Node (required for Vite dev server)
:: ------------------------------------------------------------------
node --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Node.js not found. Install from https://nodejs.org
    goto :error
)
for /f %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo  [OK] Node !NODEVER!

:: ------------------------------------------------------------------
:: Check Ollama
:: ------------------------------------------------------------------
ollama --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [WARN] Ollama not found - install from https://ollama.ai
    echo         You can still use PROVIDER=anthropic if you have an API key.
) else (
    echo  [OK] Ollama found
)

:: ------------------------------------------------------------------
:: Install Python dependencies
:: ------------------------------------------------------------------
echo.
echo  Installing Python dependencies...
pip install -r requirements.txt -q --disable-pip-version-check
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
:: Start backend (new window, stays open)
:: ------------------------------------------------------------------
set BACKEND_PORT=8000
if defined WORKSPACE_PORT set BACKEND_PORT=!WORKSPACE_PORT!

echo.
echo  Starting backend on port !BACKEND_PORT!...
start "AI Workspace - Backend" python main.py --web --host 127.0.0.1 --port !BACKEND_PORT!
if !ERRORLEVEL! neq 0 (
    echo  [ERROR] Failed to launch backend window
    goto :error
)
echo  [OK] Backend window opened

:: ------------------------------------------------------------------
:: Start frontend Vite dev server (new window, stays open via cmd /k)
:: pushd/popd sets CWD for the child process without nested quote issues
:: ------------------------------------------------------------------
echo  Starting frontend dev server...
pushd "%~dp0dashboard"
start "AI Workspace - Frontend" cmd /k "npm run dev"
set FRONT_LAUNCH=!ERRORLEVEL!
popd
if !FRONT_LAUNCH! neq 0 (
    echo  [ERROR] Failed to launch frontend window
    goto :error
)
echo  [OK] Frontend window opened

:: ------------------------------------------------------------------
:: Detect Vite's actual port (5173 or 5174) via PowerShell TCP probe.
:: Vite auto-increments when 5173 is busy. PowerShell polls up to 15s.
:: Result is written to a temp file to avoid exit-code smuggling tricks.
:: ------------------------------------------------------------------
echo  Detecting frontend port...
set "VITE_PORT_FILE=%TEMP%\ai_ws_vite_port.tmp"
if exist "!VITE_PORT_FILE!" del "!VITE_PORT_FILE!" >nul 2>&1

powershell -nologo -noprofile -command ^
  "for ($i=0;$i-lt15;$i++){foreach($p in 5173,5174){try{$t=New-Object Net.Sockets.TcpClient;$ar=$t.BeginConnect('127.0.0.1',$p,$null,$null);if($ar.AsyncWaitHandle.WaitOne(400)){$t.EndConnect($ar);$t.Close();[IO.File]::WriteAllText($env:VITE_PORT_FILE,$p.ToString());exit}; try{$t.Close()}catch{}}catch{}};Start-Sleep 1}" ^
  2>nul

set FRONTEND_PORT=5173
if exist "!VITE_PORT_FILE!" (
    set /p FRONTEND_PORT=<"!VITE_PORT_FILE!"
    del "!VITE_PORT_FILE!" >nul 2>&1
) else (
    echo  [WARN] Vite port detection timed out - defaulting to 5173
)

:: ------------------------------------------------------------------
:: Open browser at the detected frontend URL
:: ------------------------------------------------------------------
set FRONTEND_URL=http://127.0.0.1:!FRONTEND_PORT!
echo.
echo  [OK] Backend  : http://127.0.0.1:!BACKEND_PORT!  (API + WS)
echo  [OK] Frontend : !FRONTEND_URL!   (Vite dev server)
echo.
echo  Both services are running in separate windows.
echo  Close those windows to stop the services.
echo.

start "" "!FRONTEND_URL!"
goto :eof

:: ------------------------------------------------------------------
:error
echo.
pause
exit /b 1
