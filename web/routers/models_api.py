import urllib.request
import json
from fastapi import APIRouter
from config import MODEL_COSTS, HAIKU, SONNET, OPUS
from web import state

router = APIRouter(prefix="/api/models", tags=["models"])

DISPLAY_NAMES = {
    HAIKU: "Claude Haiku 4.5",
    SONNET: "Claude Sonnet 4.6",
    OPUS: "Claude Opus 4.7",
}


@router.get("")
async def get_models():
    provider = state.config.provider
    anthropic_models = [
        {
            "id": mid,
            "name": DISPLAY_NAMES.get(mid, mid),
            "input_cost": cost[0],
            "output_cost": cost[1],
            "provider": "anthropic",
        }
        for mid, cost in MODEL_COSTS.items()
    ]

    ollama_models = []
    ollama_connected = False
    if provider == "ollama":
        ollama_models, ollama_connected = _fetch_ollama_models(state.config.ollama_base_url)

    return {
        "provider": provider,
        "active_model": state.config.ollama_model if provider == "ollama" else SONNET,
        "ollama_base_url": state.config.ollama_base_url,
        "ollama_connected": ollama_connected,
        "anthropic_models": anthropic_models,
        "ollama_models": ollama_models,
    }


def _fetch_ollama_models(base_url: str) -> tuple[list[dict], bool]:
    try:
        url = f"{base_url}/api/tags"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        models = [
            {
                "id": m["name"],
                "name": m["name"],
                "size": m.get("size", 0),
                "provider": "ollama",
            }
            for m in data.get("models", [])
        ]
        return models, True
    except Exception:
        return [], False
