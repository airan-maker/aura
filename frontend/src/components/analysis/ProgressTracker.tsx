/**
 * Progress tracker component for analysis
 */

'use client';

import React from 'react';
import { AnalysisStatus } from '@/types';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Card } from '@/components/ui/Card';

interface ProgressTrackerProps {
  status: AnalysisStatus;
  progress: number;
  currentStep?: string;
  error?: string;
}

export function ProgressTracker({
  status,
  progress,
  currentStep,
  error,
}: ProgressTrackerProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return (
          <div className="animate-pulse">
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
      case 'processing':
        return (
          <div className="animate-spin">
            <svg className="w-12 h-12 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        );
      case 'completed':
        return (
          <svg className="w-12 h-12 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-12 h-12 text-danger-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return 'Waiting to start...';
      case 'processing':
        return currentStep || 'Analyzing...';
      case 'completed':
        return 'Analysis completed!';
      case 'failed':
        return error || 'Analysis failed';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return 'text-gray-600';
      case 'processing':
        return 'text-primary-600';
      case 'completed':
        return 'text-success-600';
      case 'failed':
        return 'text-danger-600';
    }
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <div className="flex flex-col items-center">
        {getStatusIcon()}
        <h2 className={`mt-4 text-xl font-semibold ${getStatusColor()}`}>
          {getStatusText()}
        </h2>
        <div className="w-full mt-6">
          <ProgressBar progress={progress} />
        </div>
        {status === 'processing' && currentStep && (
          <p className="mt-4 text-sm text-gray-600 text-center">{currentStep}</p>
        )}
        {status === 'failed' && error && (
          <div className="mt-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
            <p className="text-sm text-danger-800">{error}</p>
          </div>
        )}
      </div>
    </Card>
  );
}
