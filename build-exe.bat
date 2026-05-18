@echo off
setlocal EnableDelayedExpansion
title Build AI-Workspace.exe

echo.
echo  +------------------------------------------+
echo  ^|   Build AI-Workspace.exe (PyInstaller)   ^|
echo  +------------------------------------------+
echo.

:: ------------------------------------------------------------------
:: Require Python launcher
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
:: Install PyInstaller if absent
:: ------------------------------------------------------------------
py -c "import PyInstaller" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo  Installing PyInstaller...
    py -m pip install pyinstaller -q --disable-pip-version-check
    if !ERRORLEVEL! neq 0 (
        echo  [ERROR] Failed to install PyInstaller
        goto :error
    )
    echo  [OK] PyInstaller installed
) else (
    echo  [OK] PyInstaller present
)

:: ------------------------------------------------------------------
:: Build
:: ------------------------------------------------------------------
echo.
echo  Building dist\AI-Workspace.exe...
py -m PyInstaller ^
    --onefile ^
    --name AI-Workspace ^
    --distpath dist ^
    --workpath build\pyinstaller ^
    --specpath build\pyinstaller ^
    --console ^
    launcher.py

if !ERRORLEVEL! neq 0 (
    echo  [ERROR] PyInstaller build failed
    goto :error
)

echo.
echo  +------------------------------------------+
echo  ^|   Build complete!                        ^|
echo  ^|   Output: dist\AI-Workspace.exe          ^|
echo  ^|                                          ^|
echo  ^|   Place the EXE inside the project's    ^|
echo  ^|   dist\ folder and double-click to run. ^|
echo  +------------------------------------------+
echo.
goto :eof

:error
echo.
pause
exit /b 1
