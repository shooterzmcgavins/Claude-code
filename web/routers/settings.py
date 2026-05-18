"""GET/POST /api/settings — runtime configuration."""
from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from web import state

router = APIRouter(prefix="/api")


class SettingsUpdate(BaseModel):
    provider: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    max_tokens: Optional[int] = None


@router.get("/settings")
async def get_settings():
    cfg = state.config
    return cfg.to_dict()


@router.post("/settings")
async def update_settings(body: SettingsUpdate):
    cfg = state.config
    settings_file = state.workspace.root / "state" / "settings.json"

    # Load existing saved settings
    saved = {}
    if settings_file.exists():
        try:
            saved = json.loads(settings_file.read_text())
        except Exception:
            pass

    # Apply updates to in-memory config and save file
    if body.provider is not None:
        if body.provider not in ("anthropic", "ollama"):
            raise HTTPException(400, "provider must be 'anthropic' or 'ollama'")
        cfg.provider = body.provider
        saved["provider"] = body.provider
    if body.ollama_base_url is not None:
        cfg.ollama_base_url = body.ollama_base_url
        saved["ollama_base_url"] = body.ollama_base_url
    if body.ollama_model is not None:
        cfg.ollama_model = body.ollama_model
        saved["ollama_model"] = body.ollama_model
    if body.anthropic_api_key is not None:
        cfg.api_key = body.anthropic_api_key
        saved["anthropic_api_key"] = body.anthropic_api_key  # plaintext for now
    if body.max_tokens is not None:
        cfg.max_tokens = body.max_tokens
        saved["max_tokens"] = body.max_tokens

    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(saved, indent=2))

    return {"ok": True, "settings": cfg.to_dict()}
