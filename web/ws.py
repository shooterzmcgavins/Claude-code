"""WebSocket endpoint — all connected clients receive every EventLog broadcast."""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from web import broadcaster

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    broadcaster.add_connection(websocket)
    try:
        while True:
            await asyncio.sleep(25)
            await websocket.send_json({"type": "ping"})
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        broadcaster.remove_connection(websocket)
