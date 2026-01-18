/**
 * SEO Metrics display card
 */

'use client';

import React from 'react';
import { SEOMetrics } from '@/types';
import { Card } from '@/components/ui/Card';

interface SEOMetricsCardProps {
  metrics: SEOMetrics;
}

export function SEOMetricsCard({ metrics }: SEOMetricsCardProps) {
  const renderScore = (score: number | undefined) => {
    if (score === undefined || score === null) {
      return <span className="font-semibold text-gray-400">N/A</span>;
    }
    const color = score >= 80 ? 'text-success-600' : score >= 60 ? 'text-warning-600' : 'text-danger-600';
    return <span className={`font-semibold ${color}`}>{score.toFixed(0)}/100</span>;
  };

  const renderIssues = (issues: string[] | undefined) => {
    if (!issues || issues.length === 0) {
      return <p className="text-sm text-success-600">✓ All checks passed</p>;
    }
    return (
      <ul className="text-sm text-gray-600 space-y-1">
        {issues.map((issue, idx) => (
          <li key={idx} className="flex items-start">
            <span className="text-danger-500 mr-2">•</span>
            {issue}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <Card title="SEO Analysis">
      <div className="space-y-6">
        {/* Meta Tags */}
        {metrics.meta_tags && (
          <div>
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Meta Tags</h4>
              {renderScore(metrics.meta_tags.score)}
            </div>
            {renderIssues(metrics.meta_tags.issues)}
          </div>
        )}

        {/* Headings */}
        {metrics.headings && (
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Heading Structure</h4>
              {renderScore(metrics.headings.score)}
            </div>
            {metrics.headings.h1_text && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">H1:</span> {metrics.headings.h1_text}
              </p>
            )}
            {renderIssues(metrics.headings.issues)}
          </div>
        )}

        {/* Performance */}
        {metrics.performance && (
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Performance</h4>
              {renderScore(metrics.performance.score)}
            </div>
            {metrics.performance.load_time !== undefined && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Load Time:</span> {metrics.performance.load_time.toFixed(2)}s
              </p>
            )}
            {renderIssues(metrics.performance.issues)}
          </div>
        )}

        {/* Mobile Optimization */}
        {metrics.mobile && (
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Mobile Optimization</h4>
              {renderScore(metrics.mobile.score)}
            </div>
            {renderIssues(metrics.mobile.issues)}
          </div>
        )}

        {/* Security */}
        {metrics.security && (
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Security</h4>
              {renderScore(metrics.security.score)}
            </div>
            {metrics.security.https !== undefined && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">HTTPS:</span> {metrics.security.https ? '✓ Enabled' : '✗ Not enabled'}
              </p>
            )}
            {renderIssues(metrics.security.issues)}
          </div>
        )}

        {/* Structured Data */}
        {metrics.structured_data && (
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Structured Data</h4>
              {renderScore(metrics.structured_data.score)}
            </div>
            {metrics.structured_data.types && metrics.structured_data.types.length > 0 && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Types:</span> {metrics.structured_data.types.join(', ')}
              </p>
            )}
            {renderIssues(metrics.structured_data.issues)}
          </div>
        )}
      </div>
    </Card>
  );
}
