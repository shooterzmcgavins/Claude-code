from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web import state

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryWrite(BaseModel):
    content: str


@router.get("")
async def list_memory():
    memory_dir = state.workspace.memory
    return [
        {
            "key": p.stem,
            "size": p.stat().st_size,
            "updated_at": p.stat().st_mtime,
        }
        for p in sorted(memory_dir.glob("*.md"))
    ]


@router.get("/{key}")
async def get_memory(key: str):
    path = state.workspace.memory / f"{key}.md"
    if not path.exists():
        raise HTTPException(404, f"No memory entry for key {key!r}")
    return {"key": key, "content": path.read_text(encoding="utf-8")}


@router.put("/{key}")
async def write_memory(key: str, body: MemoryWrite):
    from datetime import datetime
    path = state.workspace.memory / f"{key}.md"
    header = f"# Memory: {key}\n\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    path.write_text(header + body.content, encoding="utf-8")
    state.event_log.log("memory.updated", {"key": key})
    return {"key": key, "size": len(body.content)}
