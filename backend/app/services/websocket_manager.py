"""
WebSocket connection manager for real-time messaging.
"""
import json
import asyncio
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """
    Manages WebSocket connections for real-time messaging.
    Supports multiple connections per user (e.g., multiple browser tabs).
    """

    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id (for reverse lookup)
        self.connection_users: Dict[WebSocket, str] = {}
        # thread_id -> set of user_ids subscribed to the thread
        self.thread_subscriptions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept a new WebSocket connection and register it.
        """
        await websocket.accept()

        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            self.connection_users[websocket] = user_id

        print(f"WebSocket connected: user={user_id}, total_connections={len(self.connection_users)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection and clean up subscriptions.
        """
        async with self._lock:
            user_id = self.connection_users.pop(websocket, None)

            if user_id and user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                # Clean up empty user entry
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

                    # Clean up thread subscriptions for this user
                    for thread_id, subscribers in list(self.thread_subscriptions.items()):
                        subscribers.discard(user_id)
                        if not subscribers:
                            del self.thread_subscriptions[thread_id]

        print(f"WebSocket disconnected: user={user_id}, total_connections={len(self.connection_users)}")

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def subscribe_to_thread(self, user_id: str, thread_id: str) -> None:
        """Subscribe a user to receive updates for a specific thread."""
        async with self._lock:
            if thread_id not in self.thread_subscriptions:
                self.thread_subscriptions[thread_id] = set()
            self.thread_subscriptions[thread_id].add(user_id)

    async def unsubscribe_from_thread(self, user_id: str, thread_id: str) -> None:
        """Unsubscribe a user from a thread."""
        async with self._lock:
            if thread_id in self.thread_subscriptions:
                self.thread_subscriptions[thread_id].discard(user_id)
                if not self.thread_subscriptions[thread_id]:
                    del self.thread_subscriptions[thread_id]

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """
        Send a message to all connections of a specific user.
        Returns True if at least one message was sent.
        """
        connections = self.active_connections.get(user_id, set())
        if not connections:
            return False

        message_json = json.dumps(message, default=str)
        sent = False

        # Send to all user connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
                sent = True
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)

        return sent

    async def broadcast_to_thread(
        self,
        thread_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to all users subscribed to a thread.
        Returns the number of users the message was sent to.
        """
        subscribers = self.thread_subscriptions.get(thread_id, set())
        sent_count = 0

        for user_id in subscribers:
            if user_id != exclude_user:
                if await self.send_to_user(user_id, message):
                    sent_count += 1

        return sent_count

    async def notify_new_message(
        self,
        thread_id: str,
        message_data: dict,
        recipient_user_id: str
    ) -> bool:
        """
        Notify a user about a new message.
        Used when the recipient might not be subscribed to the thread.
        """
        ws_message = {
            "type": "new_message",
            "payload": message_data
        }
        return await self.send_to_user(recipient_user_id, ws_message)

    async def notify_message_read(
        self,
        thread_id: str,
        reader_type: str,
        reader_user_id: str,
        other_party_user_id: str
    ) -> bool:
        """
        Notify the other party that their messages have been read.
        """
        ws_message = {
            "type": "message_read",
            "payload": {
                "thread_id": thread_id,
                "reader_type": reader_type,
                "read_at": datetime.utcnow().isoformat()
            }
        }
        return await self.send_to_user(other_party_user_id, ws_message)

    async def notify_unread_update(self, user_id: str, total_unread: int) -> bool:
        """
        Notify a user about their updated unread count.
        """
        ws_message = {
            "type": "unread_update",
            "payload": {
                "total_unread": total_unread
            }
        }
        return await self.send_to_user(user_id, ws_message)

    async def send_pong(self, websocket: WebSocket) -> None:
        """Send a pong response to a ping."""
        try:
            await websocket.send_json({"type": "pong"})
        except Exception as e:
            print(f"Error sending pong: {e}")

    def get_stats(self) -> dict:
        """Get connection statistics for monitoring."""
        return {
            "total_users": len(self.active_connections),
            "total_connections": len(self.connection_users),
            "thread_subscriptions": len(self.thread_subscriptions),
        }


# Singleton instance
ws_manager = ConnectionManager()
