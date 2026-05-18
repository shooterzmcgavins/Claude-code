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
:: Check Node
:: ------------------------------------------------------------------
set SKIP_BUILD=
node --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  [WARN] Node.js not found - frontend will use pre-built files only
    set SKIP_BUILD=1
) else (
    for /f %%v in ('node --version 2^>^&1') do set NODEVER=%%v
    echo  [OK] Node !NODEVER!
)

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
:: Build frontend
:: Flat goto structure avoids %var% parse-time expansion bug inside
:: nested parenthesized blocks.
:: ------------------------------------------------------------------
if defined SKIP_BUILD goto :skip_build
if exist "dashboard\dist\index.html" (
    echo  [OK] Frontend already built
    goto :skip_build
)

echo.
echo  Building frontend...
pushd dashboard

call npm install --silent
if !ERRORLEVEL! neq 0 (
    echo  [WARN] npm install failed - running in API-only mode
    popd
    goto :skip_build
)

call npm run build
set BUILD_RESULT=!ERRORLEVEL!
popd

if !BUILD_RESULT! neq 0 (
    echo  [WARN] Frontend build failed - running in API-only mode
) else (
    echo  [OK] Frontend built
)

:skip_build

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
:: Start server
:: ------------------------------------------------------------------
set HOST=127.0.0.1
set PORT=8000
if defined WORKSPACE_PORT set PORT=!WORKSPACE_PORT!

echo.
echo  Starting Mission Control on http://!HOST!:!PORT!
echo  Press Ctrl+C to stop.
echo.

:: Open browser after ~2s delay.
:: ping -n 3 pauses ~2s and works in both cmd.exe and Git Bash.
:: Inner cmd /c is needed so "start http://..." uses cmd's START.
start "" /b cmd /c "ping -n 3 127.0.0.1 >nul 2>&1 & start http://!HOST!:!PORT!"

python main.py --web --host !HOST! --port !PORT!
goto :eof

:: ------------------------------------------------------------------
:error
echo.
pause
exit /b 1
