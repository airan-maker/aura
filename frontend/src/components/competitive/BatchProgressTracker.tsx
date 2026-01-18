/**
 * Batch Progress Tracker for Competitive Analysis
 */

'use client';

import React from 'react';
import { AnalysisStatus, CompetitiveURLStatus } from '@/types';
import { ProgressBar } from '@/components/ui/ProgressBar';

interface BatchProgressTrackerProps {
  status: AnalysisStatus;
  progress: number;
  totalUrls: number;
  completedCount: number;
  failedCount: number;
  currentStep?: string;
  urls: CompetitiveURLStatus[];
  error?: string | null;
}

export function BatchProgressTracker({
  status,
  progress,
  totalUrls,
  completedCount,
  failedCount,
  currentStep,
  urls,
  error,
}: BatchProgressTrackerProps) {
  const getStatusIcon = (urlStatus: AnalysisStatus) => {
    switch (urlStatus) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-success-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5 text-danger-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'processing':
        return (
          <div className="w-5 h-5">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600" />
          </div>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getStatusText = (urlStatus: AnalysisStatus) => {
    switch (urlStatus) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'processing':
        return 'Processing';
      default:
        return 'Pending';
    }
  };

  const getStatusColor = (urlStatus: AnalysisStatus) => {
    switch (urlStatus) {
      case 'completed':
        return 'text-success-600';
      case 'failed':
        return 'text-danger-600';
      case 'processing':
        return 'text-primary-600';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Overall Progress</h3>
          <span className="text-sm font-medium text-gray-600">
            {completedCount}/{totalUrls} completed
          </span>
        </div>

        <ProgressBar progress={progress} className="mb-3" />

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            {currentStep || `Analyzing ${totalUrls} competitors`}
          </span>
          <span className="font-semibold text-gray-900">{Math.round(progress)}%</span>
        </div>

        {/* Status Summary */}
        {status === 'processing' && (
          <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-success-500 rounded-full" />
              {completedCount} completed
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" />
              {totalUrls - completedCount - failedCount} processing
            </span>
            {failedCount > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-danger-500 rounded-full" />
                {failedCount} failed
              </span>
            )}
          </div>
        )}

        {/* Completion Message */}
        {status === 'completed' && (
          <div className="mt-4 p-3 bg-success-50 border border-success-200 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-medium text-success-900">Analysis Complete!</p>
                <p className="text-xs text-success-700 mt-1">
                  {completedCount === totalUrls
                    ? 'All competitors analyzed successfully'
                    : `${completedCount}/${totalUrls} competitors analyzed successfully`}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-danger-50 border border-danger-200 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-medium text-danger-900">Error</p>
                <p className="text-xs text-danger-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Individual URL Progress */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Individual Progress</h3>
        <div className="space-y-3">
          {urls.map((url, index) => (
            <div
              key={url.request_id}
              className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
            >
              {/* Status Icon */}
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(url.status)}
              </div>

              {/* URL Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {url.label || `Competitor ${index + 1}`}
                    </p>
                    <p className="text-xs text-gray-500 truncate mt-0.5">{url.url}</p>
                  </div>
                  <span className={`text-xs font-medium ${getStatusColor(url.status)} whitespace-nowrap`}>
                    {getStatusText(url.status)}
                  </span>
                </div>

                {/* Progress Bar for Processing */}
                {url.status === 'processing' && (
                  <div className="mt-2">
                    <ProgressBar progress={url.progress} size="sm" />
                    <p className="text-xs text-gray-500 mt-1">{url.progress}%</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
