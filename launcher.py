"""
AI Engineering Workspace — Windows launcher.

Build into a single EXE with build-exe.bat, then run dist/AI-Workspace.exe.
The EXE lives in dist/; the project root is one level up.
"""
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

CREATE_NEW_CONSOLE = 0x00000010

BACKEND_PORT = os.environ.get("WORKSPACE_PORT", "8000")
FRONTEND_PORT = "5173"
HEALTH_URL = f"http://127.0.0.1:{BACKEND_PORT}/api/health"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        # Running as PyInstaller EXE — exe is in dist/, project root is parent
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent


def _py() -> str:
    """Return the Python executable to use."""
    # Inside EXE we can't rely on sys.executable being Python
    for candidate in ("py", "python3", "python"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True, check=True)
            return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
    return "python"


def _wait_for_backend(timeout: int = 30) -> bool:
    try:
        import urllib.request
        for _ in range(timeout):
            try:
                with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
                    if r.status == 200:
                        return True
            except Exception:
                pass
            time.sleep(1)
    except Exception:
        pass
    return False


def main() -> None:
    root = _project_root()
    print(f"Project root: {root}")

    if not (root / "main.py").exists():
        print(f"ERROR: main.py not found in {root}")
        print("Make sure AI-Workspace.exe is inside the dist/ folder of the project.")
        input("Press Enter to exit...")
        sys.exit(1)

    py = _py()
    dashboard = root / "dashboard"

    # ── Start backend ─────────────────────────────────────────────────────────
    print(f"Starting backend on port {BACKEND_PORT}...")
    backend_cmd = (
        f"title AI Workspace - Backend && "
        f"{py} main.py --web --host 127.0.0.1 --port {BACKEND_PORT}"
    )
    subprocess.Popen(
        ["cmd", "/k", backend_cmd],
        cwd=str(root),
        creationflags=CREATE_NEW_CONSOLE,
    )

    # ── Wait for health ───────────────────────────────────────────────────────
    print(f"Waiting for backend ({HEALTH_URL})...")
    if not _wait_for_backend():
        print("ERROR: Backend did not respond within 30 seconds.")
        print("Check the backend console window for errors.")
        input("Press Enter to exit...")
        sys.exit(1)
    print("Backend healthy.")

    # ── Start frontend ────────────────────────────────────────────────────────
    if not dashboard.exists():
        print(f"WARNING: dashboard/ not found at {dashboard} — skipping frontend")
    else:
        print("Starting frontend dev server...")
        subprocess.Popen(
            ["cmd", "/k", "title AI Workspace - Frontend && npm run dev"],
            cwd=str(dashboard),
            creationflags=CREATE_NEW_CONSOLE,
        )
        print(f"Waiting for Vite to initialize...")
        time.sleep(4)

    # ── Open browser ──────────────────────────────────────────────────────────
    print(f"Opening {FRONTEND_URL}")
    webbrowser.open(FRONTEND_URL)
    print("Done. Close the backend/frontend windows to stop the services.")


if __name__ == "__main__":
    main()
