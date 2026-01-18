/**
 * Competitive Analysis Batch Progress Page
 */

'use client';

import { useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { BatchProgressTracker } from '@/components/competitive/BatchProgressTracker';
import { useCompetitiveBatch } from '@/hooks/useCompetitiveBatch';
import { useCompetitiveWebSocket } from '@/hooks/useCompetitiveWebSocket';

export default function CompetitiveBatchPage() {
  const router = useRouter();
  const params = useParams();
  const batchId = params.batchId as string;

  const { batch, loading, error } = useCompetitiveBatch(batchId);
  const wsState = useCompetitiveWebSocket(batchId);

  // Use WebSocket data if available, otherwise use polling data
  const currentProgress = wsState.connected ? wsState.progress : batch?.progress ?? 0;
  const currentStep = wsState.connected ? wsState.currentStep : undefined;
  const currentStatus = wsState.connected && wsState.status ? wsState.status : batch?.status ?? 'pending';
  const currentError = wsState.error || error || batch?.error_message;
  const completedCount = wsState.connected ? wsState.completedCount : batch?.completed_count ?? 0;
  const failedCount = wsState.connected ? wsState.failedCount : batch?.failed_count ?? 0;
  const totalUrls = wsState.connected ? wsState.totalUrls : batch?.total_urls ?? 0;

  // Redirect to results when completed
  useEffect(() => {
    if (currentStatus === 'completed') {
      setTimeout(() => {
        router.push(`/competitive/${batchId}/results`);
      }, 2000);
    }
  }, [currentStatus, batchId, router]);

  if (loading && !batch) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading batch analysis...</p>
        </div>
      </div>
    );
  }

  if (error && !batch) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="max-w-md">
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
            <svg className="w-12 h-12 text-danger-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold text-danger-900 mb-2">Error Loading Batch</h2>
            <p className="text-danger-700 mb-4">{error}</p>
            <button
              onClick={() => router.push('/competitive')}
              className="bg-danger-600 text-white px-4 py-2 rounded-lg hover:bg-danger-700 transition"
            >
              Start New Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Analyzing Competitors
        </h2>
        {batch && (
          <>
            {batch.name && (
              <p className="text-lg font-medium text-gray-700 mb-1">{batch.name}</p>
            )}
            <p className="text-gray-600">
              Batch ID: <span className="font-mono text-sm">{batchId}</span>
            </p>
          </>
        )}
      </div>

      {/* Progress Tracker */}
      {batch && (
        <BatchProgressTracker
          status={currentStatus}
          progress={currentProgress}
          totalUrls={totalUrls}
          completedCount={completedCount}
          failedCount={failedCount}
          currentStep={currentStep}
          urls={batch.urls}
          error={currentError}
        />
      )}

      {/* Connection Status */}
      {wsState.connected && (
        <div className="mt-6 text-center">
          <span className="inline-flex items-center text-xs text-success-600">
            <span className="w-2 h-2 bg-success-600 rounded-full mr-2 animate-pulse" />
            Real-time updates connected
          </span>
        </div>
      )}

      {/* Completion Message */}
      {currentStatus === 'completed' && (
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Redirecting to results in 2 seconds...
          </p>
        </div>
      )}
    </div>
  );
}
