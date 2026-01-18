/**
 * Hook for managing competitive batch state with polling
 */

import { useState, useEffect, useCallback } from 'react';
import { CompetitiveBatch, CompetitiveResult } from '@/types';
import { getCompetitiveBatchStatus, getCompetitiveResults } from '@/lib/api-client';

interface UseCompetitiveBatchOptions {
  pollInterval?: number;
  autoFetch?: boolean;
}

interface UseCompetitiveBatchReturn {
  batch: CompetitiveBatch | null;
  result: CompetitiveResult | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and poll competitive batch status
 */
export function useCompetitiveBatch(
  batchId: string | null,
  options: UseCompetitiveBatchOptions = {}
): UseCompetitiveBatchReturn {
  const { pollInterval = 2000, autoFetch = true } = options;

  const [batch, setBatch] = useState<CompetitiveBatch | null>(null);
  const [result, setResult] = useState<CompetitiveResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBatch = useCallback(async () => {
    if (!batchId) {
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const data = await getCompetitiveBatchStatus(batchId);
      setBatch(data);

      // If completed, fetch full results
      if (data.status === 'completed') {
        try {
          const resultData = await getCompetitiveResults(batchId);
          setResult(resultData);
        } catch (err) {
          console.error('Failed to fetch results:', err);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch batch status');
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  // Initial fetch
  useEffect(() => {
    if (autoFetch && batchId) {
      fetchBatch();
    }
  }, [batchId, autoFetch, fetchBatch]);

  // Polling logic
  useEffect(() => {
    if (!batchId || !batch) return;

    // Stop polling if completed or failed
    if (batch.status === 'completed' || batch.status === 'failed') {
      return;
    }

    const intervalId = setInterval(() => {
      fetchBatch();
    }, pollInterval);

    return () => clearInterval(intervalId);
  }, [batchId, batch, pollInterval, fetchBatch]);

  return {
    batch,
    result,
    loading,
    error,
    refetch: fetchBatch,
  };
}
