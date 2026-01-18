/**
 * AEO Insights display card
 */

'use client';

import React from 'react';
import { AEOMetrics } from '@/types';
import { Card } from '@/components/ui/Card';

interface AEOInsightsCardProps {
  metrics: AEOMetrics;
}

export function AEOInsightsCard({ metrics }: AEOInsightsCardProps) {
  const renderClarityScore = (score: number) => {
    const color = score >= 8 ? 'text-success-600' : score >= 6 ? 'text-warning-600' : 'text-danger-600';
    return (
      <div className="flex items-center">
        <span className={`text-2xl font-bold ${color}`}>{score}</span>
        <span className="text-gray-500 text-lg ml-1">/10</span>
      </div>
    );
  };

  return (
    <Card title="AI Engine Optimization (AEO) Analysis">
      <div className="space-y-4">
        {/* Clarity Score */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex justify-between items-center">
            <h4 className="font-medium text-gray-900">Clarity Score</h4>
            {renderClarityScore(metrics.clarity_score)}
          </div>
          <p className="text-sm text-gray-600 mt-2">
            How clearly AI can understand what your website does
          </p>
        </div>

        {/* What It Does */}
        <div>
          <h4 className="font-medium text-gray-900 mb-2">What This Website Does</h4>
          <p className="text-gray-700 leading-relaxed">{metrics.what_it_does}</p>
        </div>

        {/* Products/Services */}
        {metrics.products_services && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Products & Services</h4>
            <p className="text-gray-700 leading-relaxed">{metrics.products_services}</p>
          </div>
        )}

        {/* Target Audience */}
        {metrics.target_audience && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Target Audience</h4>
            <p className="text-gray-700 leading-relaxed">{metrics.target_audience}</p>
          </div>
        )}

        {/* Unique Value */}
        {metrics.unique_value && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Unique Value Proposition</h4>
            <p className="text-gray-700 leading-relaxed">{metrics.unique_value}</p>
          </div>
        )}

        {/* Overall Impression */}
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-2">AI Overall Impression</h4>
          <p className="text-gray-700 leading-relaxed italic">{metrics.overall_impression}</p>
        </div>
      </div>
    </Card>
  );
}
