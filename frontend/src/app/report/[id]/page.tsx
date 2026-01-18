/**
 * Report dashboard page
 */

'use client';

import { useParams, useRouter } from 'next/navigation';
import { useAnalysis } from '@/hooks/useAnalysis';
import { ScoreGauge } from '@/components/report/ScoreGauge';
import { SEOMetricsCard } from '@/components/report/SEOMetricsCard';
import { AEOInsightsCard } from '@/components/report/AEOInsightsCard';
import { RecommendationList } from '@/components/report/RecommendationList';
import { Button } from '@/components/ui/Button';

export default function ReportPage() {
  const router = useRouter();
  const params = useParams();
  const requestId = params.id as string;

  const { analysis, result, loading, error } = useAnalysis(requestId);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error || !result || !analysis) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="max-w-md">
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
            <svg className="w-12 h-12 text-danger-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold text-danger-900 mb-2">Error Loading Report</h2>
            <p className="text-danger-700 mb-4">
              {error || 'Analysis not completed or results not available'}
            </p>
            <Button onClick={() => router.push('/')}>
              Go Back Home
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analysis Report</h1>
            <p className="text-gray-600 mt-1">
              <a
                href={analysis.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline"
              >
                {analysis.url}
              </a>
            </p>
          </div>
          <Button onClick={() => router.push('/')}>New Analysis</Button>
        </div>

        {/* Analysis metadata */}
        <div className="flex gap-6 text-sm text-gray-600">
          <span>
            <span className="font-medium">Duration:</span> {result.analysis_duration.toFixed(1)}s
          </span>
          <span>
            <span className="font-medium">Analyzed:</span>{' '}
            {new Date(result.created_at).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Score Gauges */}
      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-8">
          <ScoreGauge score={result.seo_score} label="SEO Score" />
        </div>
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-8">
          <ScoreGauge score={result.aeo_score} label="AEO Score" />
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid lg:grid-cols-2 gap-8 mb-8">
        <SEOMetricsCard metrics={result.seo_metrics} />
        <AEOInsightsCard metrics={result.aeo_metrics} />
      </div>

      {/* Recommendations */}
      <RecommendationList recommendations={result.recommendations} />
    </div>
  );
}
