/**
 * Analysis progress page
 */

'use client';

import { useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ProgressTracker } from '@/components/analysis/ProgressTracker';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function AnalysisPage() {
  const router = useRouter();
  const params = useParams();
  const requestId = params.id as string;

  const { analysis, loading, error } = useAnalysis(requestId);
  const wsState = useWebSocket(requestId);

  // Use WebSocket data if available, otherwise use polling data
  const currentProgress = wsState.connected ? wsState.progress : analysis?.progress ?? 0;
  const currentStep = wsState.connected ? wsState.step : analysis?.current_step;
  const currentStatus = wsState.connected && wsState.status ? wsState.status : analysis?.status ?? 'pending';
  const currentError = wsState.error || error || analysis?.error_message;

  // Redirect to report when completed
  useEffect(() => {
    if (currentStatus === 'completed') {
      setTimeout(() => {
        router.push(`/report/${requestId}`);
      }, 1500);
    }
  }, [currentStatus, requestId, router]);

  if (loading && !analysis) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="max-w-md">
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
            <svg className="w-12 h-12 text-danger-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold text-danger-900 mb-2">Error Loading Analysis</h2>
            <p className="text-danger-700 mb-4">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="bg-danger-600 text-white px-4 py-2 rounded-lg hover:bg-danger-700 transition"
            >
              Go Back Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* URL Display */}
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Analyzing Your Website</h2>
        {analysis && (
          <p className="text-gray-600">
            <span className="font-medium">URL:</span>{' '}
            <a
              href={analysis.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              {analysis.url}
            </a>
          </p>
        )}
      </div>

      {/* Progress Tracker */}
      <ProgressTracker
        status={currentStatus}
        progress={currentProgress}
        currentStep={currentStep}
        error={currentError}
      />

      {/* Connection Status */}
      {wsState.connected && (
        <div className="mt-4 text-center">
          <span className="inline-flex items-center text-xs text-success-600">
            <span className="w-2 h-2 bg-success-600 rounded-full mr-2 animate-pulse" />
            Real-time updates connected
          </span>
        </div>
      )}
    </div>
  );
}
