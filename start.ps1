#Requires -Version 5.1
<#
.SYNOPSIS
    AI Engineering Workspace — PowerShell launcher
.DESCRIPTION
    Verifies prerequisites, installs dependencies, builds the frontend,
    and starts the Mission Control web dashboard.
.PARAMETER Port
    HTTP port to listen on (default: 8000)
.PARAMETER Host
    Host to bind to (default: 127.0.0.1)
.PARAMETER NoBrowser
    Skip auto-opening the browser
.EXAMPLE
    .\start.ps1
    .\start.ps1 -Port 9000
    .\start.ps1 -NoBrowser
#>
param(
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1",
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║      AI Engineering Workspace                ║" -ForegroundColor Cyan
Write-Host "  ║      Mission Control Launcher                ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ─────────────────────────────────────────────────────────────
try {
    $pyVersion = python --version 2>&1
    Write-Host "  [OK] $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found. Install Python 3.11+ from https://python.org" -ForegroundColor Red
    exit 1
}

# ── Check Node ───────────────────────────────────────────────────────────────
$skipBuild = $false
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  [OK] Node $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Node.js not found — frontend will use pre-built files only" -ForegroundColor Yellow
    $skipBuild = $true
}

# ── Check Ollama ─────────────────────────────────────────────────────────────
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "  [OK] Ollama found" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Ollama not found — install from https://ollama.ai" -ForegroundColor Yellow
    Write-Host "         You can still use PROVIDER=anthropic if you have an API key." -ForegroundColor DarkGray
}

# ── Load .env ────────────────────────────────────────────────────────────────
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "  [OK] Loaded .env" -ForegroundColor Green
}

# ── Override port from env ────────────────────────────────────────────────────
if ($env:WORKSPACE_PORT) { $Port = [int]$env:WORKSPACE_PORT }

# ── Install Python dependencies ───────────────────────────────────────────────
Write-Host ""
Write-Host "  Installing Python dependencies..." -ForegroundColor DarkGray
try {
    pip install -r requirements.txt -q --disable-pip-version-check 2>&1 | Out-Null
    Write-Host "  [OK] Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] pip install failed: $_" -ForegroundColor Red
    exit 1
}

# ── Build frontend ────────────────────────────────────────────────────────────
if (-not $skipBuild) {
    $distIndex = "dashboard\dist\index.html"
    if (-not (Test-Path $distIndex)) {
        Write-Host ""
        Write-Host "  Building frontend..." -ForegroundColor DarkGray
        Push-Location dashboard
        try {
            npm install --silent 2>&1 | Out-Null
            npm run build --silent 2>&1 | Out-Null
            Write-Host "  [OK] Frontend built" -ForegroundColor Green
        } catch {
            Write-Host "  [WARN] Frontend build failed — running in API-only mode" -ForegroundColor Yellow
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "  [OK] Frontend already built" -ForegroundColor Green
    }
}

# ── Open browser ─────────────────────────────────────────────────────────────
$url = "http://${BindHost}:${Port}"
if (-not $NoBrowser) {
    $job = Start-Job -ScriptBlock {
        param($u)
        Start-Sleep -Seconds 2
        Start-Process $u
    } -ArgumentList $url
}

# ── Start server ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Starting Mission Control on $url" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

try {
    python main.py --web --host $BindHost --port $Port
} finally {
    if ($job) { Remove-Job $job -Force -ErrorAction SilentlyContinue }
}
