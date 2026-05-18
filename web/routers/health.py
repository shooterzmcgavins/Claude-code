"""GET /api/health — system health check for onboarding."""
from __future__ import annotations
from fastapi import APIRouter
from web import state

router = APIRouter(prefix="/api")


@router.get("/health")
async def get_health():
    cfg = state.config
    issues = []
    ollama_connected = False
    ollama_model_available = False

    if cfg.is_ollama:
        # Check Ollama connectivity
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{cfg.ollama_base_url}/api/tags")
                if r.status_code == 200:
                    ollama_connected = True
                    models = r.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    # Check if active model available (with or without tag)
                    active = cfg.ollama_model
                    ollama_model_available = any(
                        active == m or active == m.split(":")[0]
                        for m in model_names
                    )
                    if not ollama_model_available:
                        issues.append(
                            f"Model '{active}' not found in Ollama. "
                            f"Available: {', '.join(model_names[:5]) or 'none'}"
                        )
                else:
                    issues.append("Ollama returned non-200 status")
        except Exception as e:
            issues.append(
                f"Cannot connect to Ollama at {cfg.ollama_base_url}: {str(e)[:80]}"
            )
    else:
        if not cfg.api_key:
            issues.append("ANTHROPIC_API_KEY is not set")

    workspace_exists = state.workspace.root.exists()
    if not workspace_exists:
        issues.append("Workspace directory does not exist")

    return {
        "status": "ok" if not issues else "error",
        "provider": cfg.provider,
        "ollama_connected": ollama_connected,
        "ollama_model": cfg.ollama_model,
        "ollama_model_available": ollama_model_available,
        "anthropic_key_set": bool(cfg.api_key),
        "workspace_path": str(state.workspace.root.resolve()),
        "workspace_exists": workspace_exists,
        "issues": issues,
    }
