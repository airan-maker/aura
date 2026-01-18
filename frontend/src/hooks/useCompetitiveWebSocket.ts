/**
 * Hook for competitive batch WebSocket real-time updates
 */

import { useState, useEffect, useCallback } from 'react';
import { AnalysisStatus, CompetitiveBatchWebSocketMessage } from '@/types';
import { createCompetitiveWebSocket } from '@/lib/api-client';

interface UseCompetitiveWebSocketReturn {
  connected: boolean;
  status: AnalysisStatus | null;
  progress: number;
  currentStep: string | null;
  completedCount: number;
  failedCount: number;
  totalUrls: number;
  individualStatuses: Record<string, {
    progress: number;
    step: string;
    status: AnalysisStatus;
  }>;
  error: string | null;
}

/**
 * Hook to manage WebSocket connection for competitive batch progress updates
 */
export function useCompetitiveWebSocket(
  batchId: string | null
): UseCompetitiveWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [completedCount, setCompletedCount] = useState(0);
  const [failedCount, setFailedCount] = useState(0);
  const [totalUrls, setTotalUrls] = useState(0);
  const [individualStatuses, setIndividualStatuses] = useState<Record<string, {
    progress: number;
    step: string;
    status: AnalysisStatus;
  }>>({});
  const [error, setError] = useState<string | null>(null);

  const handleMessage = useCallback((data: CompetitiveBatchWebSocketMessage) => {
    if (data.status) {
      setStatus(data.status);
    }
    if (data.progress !== undefined) {
      setProgress(data.progress);
    }
    if (data.current_step) {
      setCurrentStep(data.current_step);
    }
    if (data.completed_count !== undefined) {
      setCompletedCount(data.completed_count);
    }
    if (data.failed_count !== undefined) {
      setFailedCount(data.failed_count);
    }
    if (data.total_urls !== undefined) {
      setTotalUrls(data.total_urls);
    }
    if (data.individual_statuses) {
      setIndividualStatuses(data.individual_statuses);
    }
    if (data.error) {
      setError(data.error);
    }
  }, []);

  useEffect(() => {
    if (!batchId) return;

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;
    let pingInterval: NodeJS.Timeout;

    const connect = () => {
      try {
        ws = createCompetitiveWebSocket(batchId);

        ws.onopen = () => {
          setConnected(true);
          setError(null);

          // Send ping every 30 seconds to keep connection alive
          pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type !== 'pong') {
              handleMessage(data);
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onerror = (event) => {
          console.error('WebSocket error:', event);
          setError('Connection error');
        };

        ws.onclose = () => {
          setConnected(false);
          clearInterval(pingInterval);

          // Attempt reconnect after 3 seconds (only if not completed/failed)
          if (status !== 'completed' && status !== 'failed') {
            reconnectTimeout = setTimeout(connect, 3000);
          }
        };
      } catch (err) {
        console.error('Failed to create WebSocket:', err);
        setError('Failed to establish connection');
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      clearInterval(pingInterval);
      if (ws) {
        ws.close();
      }
    };
  }, [batchId, status, handleMessage]);

  return {
    connected,
    status,
    progress,
    currentStep,
    completedCount,
    failedCount,
    totalUrls,
    individualStatuses,
    error,
  };
}
