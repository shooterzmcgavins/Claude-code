"""FastAPI application — Mission Control backend."""
from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import Config
from core.workspace import Workspace
from core import events as events_module
from web import broadcaster, state
from web.ws import router as ws_router
from web.routers import (
    tasks, events as events_router, agents, reports,
    memory, models_api, chat, approvals,
    health, files,
)
from web.routers import settings as settings_router

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "dashboard" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Capture the running event loop for thread-safe WS broadcasting
    loop = asyncio.get_event_loop()
    broadcaster.set_loop(loop)

    # Wire EventLog → broadcaster
    events_module.set_broadcast_hook(
        lambda entry: broadcaster.emit({"type": "event.log", **entry})
    )

    # Load persisted settings
    settings_file = state.workspace.root / "state" / "settings.json"
    if settings_file.exists():
        import json as _json
        try:
            saved = _json.loads(settings_file.read_text())
            if saved.get("provider"):
                state.config.provider = saved["provider"]
            if saved.get("ollama_base_url"):
                state.config.ollama_base_url = saved["ollama_base_url"]
            if saved.get("ollama_model"):
                state.config.ollama_model = saved["ollama_model"]
            if saved.get("anthropic_api_key"):
                state.config.api_key = saved["anthropic_api_key"]
            if saved.get("max_tokens"):
                state.config.max_tokens = saved["max_tokens"]
        except Exception:
            pass

    log.info("Mission Control started")
    yield

    state.executor.shutdown(wait=False)
    log.info("Mission Control stopped")


def create_app(cfg: Config, workspace: Workspace) -> FastAPI:
    # Initialize shared state
    state.init(cfg, workspace)

    app = FastAPI(
        title="AI Workspace Mission Control",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(ws_router)
    app.include_router(chat.router)
    app.include_router(tasks.router)
    app.include_router(events_router.router)
    app.include_router(agents.router)
    app.include_router(reports.router)
    app.include_router(memory.router)
    app.include_router(models_api.router)
    app.include_router(approvals.router)
    app.include_router(health.router)
    app.include_router(settings_router.router)
    app.include_router(files.router)

    # Serve built frontend (production)
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app
