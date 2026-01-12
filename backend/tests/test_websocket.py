"""
Tests for WebSocket functionality.

Covers:
- WebSocket connection manager
- Connection lifecycle (connect, disconnect)
- Message broadcasting
- Thread subscriptions
- Real-time notifications
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import WebSocket

from app.services.websocket_manager import ConnectionManager


class TestConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh connection manager."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = MagicMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    # ============ Connection Tests ============

    @pytest.mark.asyncio
    async def test_connect_new_user(self, manager, mock_websocket):
        """Test connecting a new user."""
        await manager.connect(mock_websocket, "user123")

        assert "user123" in manager.active_connections
        assert mock_websocket in manager.active_connections["user123"]
        assert manager.connection_users[mock_websocket] == "user123"
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple_connections_same_user(self, manager):
        """Test multiple connections for same user (multiple tabs)."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "user123")
        await manager.connect(ws2, "user123")

        assert len(manager.active_connections["user123"]) == 2
        assert ws1 in manager.active_connections["user123"]
        assert ws2 in manager.active_connections["user123"]

    @pytest.mark.asyncio
    async def test_disconnect_single_connection(self, manager, mock_websocket):
        """Test disconnecting a user with single connection."""
        await manager.connect(mock_websocket, "user123")
        await manager.disconnect(mock_websocket)

        assert "user123" not in manager.active_connections
        assert mock_websocket not in manager.connection_users

    @pytest.mark.asyncio
    async def test_disconnect_one_of_multiple_connections(self, manager):
        """Test disconnecting one of multiple connections."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "user123")
        await manager.connect(ws2, "user123")
        await manager.disconnect(ws1)

        assert "user123" in manager.active_connections
        assert len(manager.active_connections["user123"]) == 1
        assert ws2 in manager.active_connections["user123"]

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_subscriptions(self, manager, mock_websocket):
        """Test that disconnecting cleans up thread subscriptions."""
        await manager.connect(mock_websocket, "user123")
        await manager.subscribe_to_thread("user123", "thread1")
        await manager.subscribe_to_thread("user123", "thread2")

        await manager.disconnect(mock_websocket)

        # Subscriptions should be cleaned up
        assert "thread1" not in manager.thread_subscriptions or \
               "user123" not in manager.thread_subscriptions.get("thread1", set())
        assert "thread2" not in manager.thread_subscriptions or \
               "user123" not in manager.thread_subscriptions.get("thread2", set())

    # ============ User Online Status Tests ============

    @pytest.mark.asyncio
    async def test_is_user_online_connected(self, manager, mock_websocket):
        """Test user is online when connected."""
        await manager.connect(mock_websocket, "user123")
        assert manager.is_user_online("user123") is True

    @pytest.mark.asyncio
    async def test_is_user_online_disconnected(self, manager, mock_websocket):
        """Test user is offline when disconnected."""
        await manager.connect(mock_websocket, "user123")
        await manager.disconnect(mock_websocket)
        assert manager.is_user_online("user123") is False

    def test_is_user_online_never_connected(self, manager):
        """Test user is offline when never connected."""
        assert manager.is_user_online("unknown_user") is False

    # ============ Thread Subscription Tests ============

    @pytest.mark.asyncio
    async def test_subscribe_to_thread(self, manager, mock_websocket):
        """Test subscribing to a thread."""
        await manager.connect(mock_websocket, "user123")
        await manager.subscribe_to_thread("user123", "thread1")

        assert "thread1" in manager.thread_subscriptions
        assert "user123" in manager.thread_subscriptions["thread1"]

    @pytest.mark.asyncio
    async def test_unsubscribe_from_thread(self, manager, mock_websocket):
        """Test unsubscribing from a thread."""
        await manager.connect(mock_websocket, "user123")
        await manager.subscribe_to_thread("user123", "thread1")
        await manager.unsubscribe_from_thread("user123", "thread1")

        assert "thread1" not in manager.thread_subscriptions or \
               "user123" not in manager.thread_subscriptions.get("thread1", set())

    @pytest.mark.asyncio
    async def test_multiple_users_subscribe_to_same_thread(self, manager):
        """Test multiple users subscribing to same thread."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")
        await manager.subscribe_to_thread("user1", "thread1")
        await manager.subscribe_to_thread("user2", "thread1")

        assert len(manager.thread_subscriptions["thread1"]) == 2

    # ============ Message Sending Tests ============

    @pytest.mark.asyncio
    async def test_send_to_user_success(self, manager, mock_websocket):
        """Test sending message to connected user."""
        await manager.connect(mock_websocket, "user123")

        result = await manager.send_to_user("user123", {"type": "test", "data": "hello"})

        assert result is True
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "test"

    @pytest.mark.asyncio
    async def test_send_to_user_not_connected(self, manager):
        """Test sending message to non-connected user returns False."""
        result = await manager.send_to_user("unknown_user", {"type": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_all_user_connections(self, manager):
        """Test message sent to all connections of a user."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()

        await manager.connect(ws1, "user123")
        await manager.connect(ws2, "user123")

        await manager.send_to_user("user123", {"type": "test"})

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_handles_disconnected_socket(self, manager):
        """Test sending handles disconnected sockets gracefully."""
        ws = MagicMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock(side_effect=Exception("Connection closed"))

        await manager.connect(ws, "user123")
        result = await manager.send_to_user("user123", {"type": "test"})

        # Should handle error and clean up
        assert result is False or "user123" not in manager.active_connections

    # ============ Broadcast Tests ============

    @pytest.mark.asyncio
    async def test_broadcast_to_thread_subscribers(self, manager):
        """Test broadcasting to all thread subscribers."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")
        await manager.subscribe_to_thread("user1", "thread1")
        await manager.subscribe_to_thread("user2", "thread1")

        count = await manager.broadcast_to_thread("thread1", {"type": "broadcast"})

        assert count == 2
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_excludes_user(self, manager):
        """Test broadcast can exclude specific user."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")
        await manager.subscribe_to_thread("user1", "thread1")
        await manager.subscribe_to_thread("user2", "thread1")

        count = await manager.broadcast_to_thread(
            "thread1",
            {"type": "broadcast"},
            exclude_user="user1"
        )

        assert count == 1
        ws1.send_text.assert_not_called()
        ws2.send_text.assert_called_once()

    # ============ Notification Tests ============

    @pytest.mark.asyncio
    async def test_notify_new_message(self, manager, mock_websocket):
        """Test new message notification."""
        await manager.connect(mock_websocket, "user123")

        message_data = {
            "id": "msg1",
            "content": "Hello",
            "sender_type": "DOCTOR"
        }

        result = await manager.notify_new_message(
            thread_id="thread1",
            message_data=message_data,
            recipient_user_id="user123"
        )

        assert result is True
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "new_message"
        assert sent_data["payload"]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_notify_message_read(self, manager, mock_websocket):
        """Test message read notification."""
        await manager.connect(mock_websocket, "user123")

        result = await manager.notify_message_read(
            thread_id="thread1",
            reader_type="PATIENT",
            reader_user_id="patient1",
            other_party_user_id="user123"
        )

        assert result is True
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "message_read"
        assert sent_data["payload"]["thread_id"] == "thread1"
        assert sent_data["payload"]["reader_type"] == "PATIENT"

    @pytest.mark.asyncio
    async def test_notify_unread_update(self, manager, mock_websocket):
        """Test unread count update notification."""
        await manager.connect(mock_websocket, "user123")

        result = await manager.notify_unread_update("user123", total_unread=5)

        assert result is True
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "unread_update"
        assert sent_data["payload"]["total_unread"] == 5

    # ============ Pong Tests ============

    @pytest.mark.asyncio
    async def test_send_pong(self, manager, mock_websocket):
        """Test sending pong response."""
        await manager.send_pong(mock_websocket)

        mock_websocket.send_json.assert_called_once_with({"type": "pong"})

    @pytest.mark.asyncio
    async def test_send_pong_handles_error(self, manager):
        """Test pong handles connection errors."""
        ws = MagicMock(spec=WebSocket)
        ws.send_json = AsyncMock(side_effect=Exception("Connection error"))

        # Should not raise
        await manager.send_pong(ws)

    # ============ Stats Tests ============

    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """Test getting connection statistics."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")
        await manager.subscribe_to_thread("user1", "thread1")

        stats = manager.get_stats()

        assert stats["total_users"] == 2
        assert stats["total_connections"] == 2
        assert stats["thread_subscriptions"] == 1


class TestWebSocketEndpoint:
    """Test WebSocket endpoint integration."""

    @pytest.mark.asyncio
    async def test_websocket_invalid_token_rejected(self, client):
        """Test WebSocket rejects invalid token."""
        # Note: Testing actual WebSocket connections requires different approach
        # This test documents expected behavior
        pass  # WebSocket testing requires httpx websocket support or starlette testclient

    @pytest.mark.asyncio
    async def test_websocket_missing_token_rejected(self, client):
        """Test WebSocket rejects missing token."""
        pass  # WebSocket testing requires specific setup


class TestWebSocketMessageHandling:
    """Test WebSocket message handling logic."""

    @pytest.mark.asyncio
    async def test_handle_ping_message(self):
        """Test handling ping message returns pong."""
        from app.api.websocket import handle_client_message
        from app.services.websocket_manager import ws_manager

        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()

        await handle_client_message(mock_ws, "user123", {"type": "ping"})

        mock_ws.send_json.assert_called_with({"type": "pong"})

    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self):
        """Test handling subscribe message."""
        from app.api.websocket import handle_client_message
        from app.services.websocket_manager import ws_manager

        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()

        # Connect first
        mock_ws.accept = AsyncMock()
        await ws_manager.connect(mock_ws, "user123")

        await handle_client_message(
            mock_ws,
            "user123",
            {"type": "subscribe_thread", "thread_id": "thread1"}
        )

        mock_ws.send_json.assert_called_with({
            "type": "subscribed",
            "payload": {"thread_id": "thread1"}
        })

        # Clean up
        await ws_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_handle_unsubscribe_message(self):
        """Test handling unsubscribe message."""
        from app.api.websocket import handle_client_message
        from app.services.websocket_manager import ws_manager

        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        mock_ws.accept = AsyncMock()

        # Connect and subscribe first
        await ws_manager.connect(mock_ws, "user123")
        await ws_manager.subscribe_to_thread("user123", "thread1")

        await handle_client_message(
            mock_ws,
            "user123",
            {"type": "unsubscribe_thread", "thread_id": "thread1"}
        )

        mock_ws.send_json.assert_called_with({
            "type": "unsubscribed",
            "payload": {"thread_id": "thread1"}
        })

        # Clean up
        await ws_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_handle_unknown_message_type(self):
        """Test handling unknown message type returns error."""
        from app.api.websocket import handle_client_message

        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()

        await handle_client_message(
            mock_ws,
            "user123",
            {"type": "unknown_type"}
        )

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert "unknown_type" in call_args["payload"]["message"].lower()


class TestConcurrency:
    """Test concurrent WebSocket operations."""

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test handling many concurrent connections."""
        manager = ConnectionManager()

        async def connect_user(user_id: str):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            await manager.connect(ws, user_id)
            return ws

        # Connect 100 users concurrently
        tasks = [connect_user(f"user{i}") for i in range(100)]
        websockets = await asyncio.gather(*tasks)

        assert len(manager.active_connections) == 100
        assert len(manager.connection_users) == 100

        # Disconnect all
        disconnect_tasks = [manager.disconnect(ws) for ws in websockets]
        await asyncio.gather(*disconnect_tasks)

        assert len(manager.active_connections) == 0
        assert len(manager.connection_users) == 0

    @pytest.mark.asyncio
    async def test_concurrent_broadcasts(self):
        """Test concurrent broadcasts don't cause issues."""
        manager = ConnectionManager()

        # Setup connections
        websockets = []
        for i in range(10):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            await manager.connect(ws, f"user{i}")
            await manager.subscribe_to_thread(f"user{i}", "thread1")
            websockets.append(ws)

        # Broadcast concurrently
        async def broadcast():
            await manager.broadcast_to_thread("thread1", {"type": "test"})

        tasks = [broadcast() for _ in range(50)]
        await asyncio.gather(*tasks)

        # Each websocket should have received multiple messages
        for ws in websockets:
            assert ws.send_text.call_count == 50

        # Cleanup
        for ws in websockets:
            await manager.disconnect(ws)
