/**
 * Hook for managing analysis state with polling
 */

import { useState, useEffect, useCallback } from 'react';
import { AnalysisRequest, AnalysisResult } from '@/types';
import { getAnalysisStatus, getAnalysisResults } from '@/lib/api-client';

interface UseAnalysisOptions {
  pollInterval?: number;
  autoFetch?: boolean;
}

interface UseAnalysisReturn {
  analysis: AnalysisRequest | null;
  result: AnalysisResult | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and poll analysis status
 */
export function useAnalysis(
  requestId: string | null,
  options: UseAnalysisOptions = {}
): UseAnalysisReturn {
  const { pollInterval = 2000, autoFetch = true } = options;

  const [analysis, setAnalysis] = useState<AnalysisRequest | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!requestId) {
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const data = await getAnalysisStatus(requestId);
      setAnalysis(data);

      // If completed, fetch results
      if (data.status === 'completed') {
        try {
          const resultData = await getAnalysisResults(requestId);
          setResult(resultData);
        } catch (err) {
          console.error('Failed to fetch results:', err);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analysis');
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  // Initial fetch
  useEffect(() => {
    if (autoFetch && requestId) {
      fetchAnalysis();
    }
  }, [requestId, autoFetch, fetchAnalysis]);

  // Polling logic
  useEffect(() => {
    if (!requestId || !analysis) return;

    // Stop polling if completed or failed
    if (analysis.status === 'completed' || analysis.status === 'failed') {
      return;
    }

    const intervalId = setInterval(() => {
      fetchAnalysis();
    }, pollInterval);

    return () => clearInterval(intervalId);
  }, [requestId, analysis, pollInterval, fetchAnalysis]);

  return {
    analysis,
    result,
    loading,
    error,
    refetch: fetchAnalysis,
  };
}
