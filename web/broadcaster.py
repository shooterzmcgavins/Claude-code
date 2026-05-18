"""Thread-safe WebSocket broadcaster.

Agent threads call emit() synchronously.
emit() schedules the coroutine on the main asyncio event loop
using run_coroutine_threadsafe so it never blocks the agent.
"""
import asyncio
import logging
from typing import Any

_connections: set = set()
_loop: asyncio.AbstractEventLoop | None = None
log = logging.getLogger(__name__)


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


def add_connection(ws: Any) -> None:
    _connections.add(ws)


def remove_connection(ws: Any) -> None:
    _connections.discard(ws)


async def broadcast(data: dict) -> None:
    dead = set()
    for ws in list(_connections):
        try:
            await ws.send_json(data)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)


def emit(data: dict) -> None:
    """Broadcast from any thread. No-ops if no loop or no connections."""
    if not _connections or _loop is None or _loop.is_closed():
        return
    asyncio.run_coroutine_threadsafe(broadcast(data), _loop)
