/**
 * Competitive Analysis Results Page
 */

'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCompetitiveBatch } from '@/hooks/useCompetitiveBatch';
import { ComparisonGrid } from '@/components/competitive/ComparisonGrid';
import { CompetitiveInsightsPanel } from '@/components/competitive/CompetitiveInsightsPanel';
import { BenchmarkChart } from '@/components/competitive/BenchmarkChart';

export default function CompetitiveResultsPage() {
  const params = useParams();
  const router = useRouter();
  const batchId = params.batchId as string;

  const { batch, result, loading, error } = useCompetitiveBatch(batchId);

  if (loading && !result) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="max-w-md">
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
            <svg className="w-12 h-12 text-danger-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold text-danger-900 mb-2">
              {batch?.status === 'completed'
                ? 'Results Not Found'
                : 'Analysis Not Completed'}
            </h2>
            <p className="text-danger-700 mb-4">
              {error ||
                'The analysis has not completed yet or results are not available.'}
            </p>
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

  const { comparison } = result;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Competitive Analysis Results
            </h1>
            {batch?.name && (
              <p className="text-lg text-gray-600">{batch.name}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/competitive')}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium"
            >
              New Analysis
            </button>
            <button
              onClick={() => window.print()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Export
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-600">Competitors</p>
                <p className="text-xl font-bold text-gray-900">
                  {batch?.total_urls || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-600">SEO Leader</p>
                <p className="text-lg font-bold text-gray-900">
                  {Math.round(comparison.market_leader.seo.score)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-600">AEO Leader</p>
                <p className="text-lg font-bold text-gray-900">
                  {Math.round(comparison.market_leader.aeo.score)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-warning-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-600">Opportunities</p>
                <p className="text-xl font-bold text-gray-900">
                  {comparison.opportunities.length}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-8">
        {/* AI Insights Panel */}
        <CompetitiveInsightsPanel
          insights={comparison.insights}
          opportunities={comparison.opportunities}
          threats={comparison.threats}
        />

        {/* Benchmark Chart */}
        <BenchmarkChart
          seoRankings={comparison.seo_rankings}
          aeoRankings={comparison.aeo_rankings}
          marketAverage={comparison.market_average}
        />

        {/* Comparison Grid */}
        <ComparisonGrid
          seoRankings={comparison.seo_rankings}
          aeoRankings={comparison.aeo_rankings}
          marketAverage={comparison.market_average}
        />
      </div>

      {/* Footer Actions */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-600">
            Analysis completed on{' '}
            {batch?.completed_at
              ? new Date(batch.completed_at).toLocaleString()
              : 'N/A'}
          </p>
          <button
            onClick={() => router.push('/competitive')}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
          >
            Start New Competitive Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
