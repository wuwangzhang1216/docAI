'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { api } from '@/lib/api';

// WebSocket message types
export interface WSMessage {
  type: 'new_message' | 'message_read' | 'unread_update' | 'pong' | 'subscribed' | 'unsubscribed' | 'error' | 'ping';
  payload?: Record<string, unknown>;
}

export interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (message: Record<string, unknown>) => void;
  subscribeToThread: (threadId: string) => void;
  unsubscribeFromThread: (threadId: string) => void;
  connect: () => void;
  disconnect: () => void;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws';
const HEARTBEAT_INTERVAL = 25000; // 25 seconds
const DEFAULT_RECONNECT_INTERVAL = 3000; // 3 seconds
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    autoConnect = true,
    reconnectInterval = DEFAULT_RECONNECT_INTERVAL,
    maxReconnectAttempts = DEFAULT_MAX_RECONNECT_ATTEMPTS,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnectRef = useRef(false);

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    const token = api.getToken();
    if (!token) {
      console.warn('No auth token available for WebSocket connection');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    isManualDisconnectRef.current = false;

    try {
      const wsUrl = `${WS_BASE_URL}?token=${encodeURIComponent(token)}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);

          // Handle ping from server
          if (message.type === 'ping') {
            wsRef.current?.send(JSON.stringify({ type: 'pong' }));
            return;
          }

          onMessage?.(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        clearTimers();
        onDisconnect?.();

        // Attempt reconnect if not manual disconnect
        if (!isManualDisconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Attempting reconnect ${reconnectAttemptsRef.current}/${maxReconnectAttempts}...`);
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [onConnect, onDisconnect, onMessage, startHeartbeat, clearTimers, reconnectInterval, maxReconnectAttempts]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, [clearTimers]);

  // Send message
  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Subscribe to thread updates
  const subscribeToThread = useCallback((threadId: string) => {
    sendMessage({ type: 'subscribe_thread', thread_id: threadId });
  }, [sendMessage]);

  // Unsubscribe from thread updates
  const unsubscribeFromThread = useCallback((threadId: string) => {
    sendMessage({ type: 'unsubscribe_thread', thread_id: threadId });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    isConnected,
    sendMessage,
    subscribeToThread,
    unsubscribeFromThread,
    connect,
    disconnect,
  };
}
