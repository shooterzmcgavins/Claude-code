from fastapi import APIRouter, HTTPException
from web import state

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def list_reports():
    reports_dir = state.workspace.reports
    items = []
    for path in sorted(reports_dir.glob("TASK-*.md"), reverse=True):
        task = state.task_store.load(path.stem)
        items.append({
            "task_id": path.stem,
            "title": task.title if task else path.stem,
            "agent": task.agent if task else None,
            "created_at": task.created_at if task else None,
            "size": path.stat().st_size,
        })
    return items


@router.get("/{task_id}")
async def get_report(task_id: str):
    path = state.workspace.reports / f"{task_id.upper()}.md"
    if not path.exists():
        raise HTTPException(404, f"No report for {task_id}")
    return {"task_id": task_id.upper(), "content": path.read_text(encoding="utf-8")}
