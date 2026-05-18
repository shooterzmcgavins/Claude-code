from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web import state

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ResolveRequest(BaseModel):
    approved: bool


@router.get("/pending")
async def pending_approvals():
    return state.approval_manager.pending()


@router.post("/{approval_id}/resolve")
async def resolve_approval(approval_id: str, body: ResolveRequest):
    ok = state.approval_manager.resolve(approval_id, body.approved)
    if not ok:
        raise HTTPException(404, f"Approval {approval_id} not found or already resolved")
    return {"approval_id": approval_id, "approved": body.approved}
