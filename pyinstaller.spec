# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for AI Engineering Workspace.

Usage:
    pip install pyinstaller
    pyinstaller pyinstaller.spec

Output: dist/AI-Workspace[.exe]

The bundled app:
  - Starts the FastAPI backend
  - Serves the pre-built React frontend from dashboard/dist/
  - Opens the browser automatically
  - Keeps logs in workspace/logs/
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)  # noqa: F821 — PyInstaller injects SPECPATH

block_cipher = None

# Collect all Python source packages
added_files = [
    # Frontend static assets
    (str(ROOT / "dashboard" / "dist"), "dashboard/dist"),
    # Workspace agent starter templates (embedded in workspace.py but include for safety)
    (str(ROOT / "workspace"), "workspace") if (ROOT / "workspace").exists() else (".", "."),
]

# Filter out non-existent sources
added_files = [(src, dst) for src, dst in added_files if Path(src).exists()]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # FastAPI / Starlette
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "starlette.staticfiles",
        "starlette.middleware",
        "starlette.middleware.cors",
        "anyio",
        "anyio._backends._asyncio",
        # HTTP
        "httpx",
        "httpcore",
        # Anthropic SDK (optional)
        "anthropic",
        # OpenAI SDK for Ollama compat
        "openai",
        # Other
        "dotenv",
        "aiofiles",
        "multipart",
        "email",
        "email.mime",
        "email.mime.multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "PIL"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AI-Workspace",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # keep console for log output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # set to "icon.ico" if you add one
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AI-Workspace",
)
