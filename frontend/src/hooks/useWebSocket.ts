/**
 * Hook for WebSocket real-time updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketMessage, AnalysisStatus } from '@/types';
import { createWebSocket } from '@/lib/api-client';

interface WebSocketState {
  connected: boolean;
  progress: number;
  step: string;
  status: AnalysisStatus | null;
  error: string | null;
}

/**
 * Hook for WebSocket connection to analysis updates
 */
export function useWebSocket(requestId: string | null) {
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    progress: 0,
    step: '',
    status: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (!requestId) return;

    try {
      const ws = createWebSocket(requestId);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setState(prev => ({ ...prev, connected: true, error: null }));

        // Send ping every 30 seconds to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === 'progress' || message.type === 'completed') {
            setState(prev => ({
              ...prev,
              progress: message.progress ?? prev.progress,
              step: message.step ?? prev.step,
              status: message.status ?? prev.status,
            }));
          } else if (message.type === 'error') {
            setState(prev => ({
              ...prev,
              error: message.error ?? 'Unknown error',
              status: 'failed',
            }));
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, error: 'WebSocket connection error' }));
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setState(prev => ({ ...prev, connected: false }));

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }

        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (state.status !== 'completed' && state.status !== 'failed') {
            console.log('Attempting to reconnect...');
            connect();
          }
        }, 3000);
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setState(prev => ({ ...prev, error: 'Failed to create WebSocket connection' }));
    }
  }, [requestId, state.status]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
  }, []);

  useEffect(() => {
    if (requestId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [requestId, connect, disconnect]);

  return {
    ...state,
    disconnect,
    reconnect: connect,
  };
}
