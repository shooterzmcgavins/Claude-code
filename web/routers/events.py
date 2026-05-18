from fastapi import APIRouter
from typing import Optional
from web import state

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
async def recent_events(n: int = 50, agent: Optional[str] = None, type: Optional[str] = None):
    entries = state.event_log.recent(n * 3)  # fetch extra, then filter
    if agent:
        entries = [e for e in entries if e.get("agent") == agent]
    if type:
        entries = [e for e in entries if e.get("type") == type]
    return entries[:n]
