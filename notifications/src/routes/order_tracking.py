from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.websockets import ws_order_status_manager

router = APIRouter(prefix="/order-tracking", tags=["Order Tracking"])

@router.websocket("/{order_id}/ws")
async def websocket_order_tracking(websocket: WebSocket, order_id: str):
    await websocket.accept()
    await ws_order_status_manager.connect(order_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_order_status_manager.disconnect(order_id, websocket)