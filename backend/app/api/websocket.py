"""
WebSocket endpoint for real-time messaging.
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.utils.security import decode_token
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 30


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time messaging.

    Authentication:
        Connect with ?token=<jwt_token>

    Client -> Server messages:
        {"type": "ping"} - Heartbeat ping
        {"type": "subscribe_thread", "thread_id": "xxx"} - Subscribe to thread updates
        {"type": "unsubscribe_thread", "thread_id": "xxx"} - Unsubscribe from thread

    Server -> Client messages:
        {"type": "pong"} - Heartbeat response
        {"type": "new_message", "payload": {...}} - New message notification
        {"type": "message_read", "payload": {...}} - Message read notification
        {"type": "unread_update", "payload": {"total_unread": N}} - Unread count update
    """
    # Authenticate the connection
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token: missing user ID")
            return
    except JWTError as e:
        await websocket.close(code=4001, reason=f"Invalid token: {str(e)}")
        return

    # Connect the WebSocket
    await ws_manager.connect(websocket, user_id)

    try:
        # Main message loop
        while True:
            try:
                # Wait for messages with timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_INTERVAL * 2
                )

                # Parse and handle message
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, user_id, message)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Invalid JSON format"}
                    })

            except asyncio.TimeoutError:
                # No message received, send a ping to check connection
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    # Connection lost
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
    finally:
        await ws_manager.disconnect(websocket)


async def handle_client_message(
    websocket: WebSocket,
    user_id: str,
    message: dict
) -> None:
    """Handle incoming WebSocket messages from clients."""
    msg_type = message.get("type")

    if msg_type == "ping":
        await ws_manager.send_pong(websocket)

    elif msg_type == "subscribe_thread":
        thread_id = message.get("thread_id")
        if thread_id:
            await ws_manager.subscribe_to_thread(user_id, thread_id)
            await websocket.send_json({
                "type": "subscribed",
                "payload": {"thread_id": thread_id}
            })

    elif msg_type == "unsubscribe_thread":
        thread_id = message.get("thread_id")
        if thread_id:
            await ws_manager.unsubscribe_from_thread(user_id, thread_id)
            await websocket.send_json({
                "type": "unsubscribed",
                "payload": {"thread_id": thread_id}
            })

    else:
        await websocket.send_json({
            "type": "error",
            "payload": {"message": f"Unknown message type: {msg_type}"}
        })
