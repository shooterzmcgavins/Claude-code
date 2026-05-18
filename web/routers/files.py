"""File manager API — browse and edit workspace files."""
from __future__ import annotations
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from web import state

router = APIRouter(prefix="/api/files")

ALLOWED_DIRS = [
    "agents", "memory", "reports", "tasks", "workflows",
    "scripts", "dashboards", "vault", "chats",
]


def _resolve_safe(rel_path: str) -> Path:
    """Resolve a relative workspace path and enforce it stays inside workspace."""
    root = state.workspace.root.resolve()
    target = (root / rel_path).resolve()
    if not str(target).startswith(str(root)):
        raise HTTPException(403, "Path outside workspace")
    return target


@router.get("")
async def list_files(path: str = Query(default=".")):
    target = _resolve_safe(path)
    if not target.exists():
        raise HTTPException(404, f"Path not found: {path}")
    if not target.is_dir():
        raise HTTPException(400, "Path is not a directory")

    entries = []
    for item in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name)):
        stat = item.stat()
        entries.append({
            "name": item.name,
            "path": str(item.relative_to(state.workspace.root.resolve())),
            "type": "dir" if item.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "ext": item.suffix.lower() if item.is_file() else "",
        })

    return {
        "path": path,
        "entries": entries,
    }


@router.get("/read")
async def read_file_content(path: str = Query(...)):
    target = _resolve_safe(path)
    if not target.exists():
        raise HTTPException(404, "File not found")
    if not target.is_file():
        raise HTTPException(400, "Path is not a file")
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"path": path, "content": content}


class WriteBody(BaseModel):
    path: str
    content: str


@router.post("/write")
async def write_file_content(body: WriteBody):
    target = _resolve_safe(body.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.content, encoding="utf-8")
    return {"ok": True}


class DeleteBody(BaseModel):
    path: str


@router.post("/delete")
async def delete_file(body: DeleteBody):
    target = _resolve_safe(body.path)
    if not target.exists():
        raise HTTPException(404, "Not found")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"ok": True}


class RenameBody(BaseModel):
    from_path: str
    to_path: str


@router.post("/rename")
async def rename_file(body: RenameBody):
    src = _resolve_safe(body.from_path)
    dst = _resolve_safe(body.to_path)
    if not src.exists():
        raise HTTPException(404, "Source not found")
    src.rename(dst)
    return {"ok": True}


class CreateBody(BaseModel):
    path: str
    type: str = "file"
    content: str = ""


@router.post("/create")
async def create_entry(body: CreateBody):
    target = _resolve_safe(body.path)
    if target.exists():
        raise HTTPException(409, "Already exists")
    if body.type == "dir":
        target.mkdir(parents=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.content, encoding="utf-8")
    return {"ok": True}
