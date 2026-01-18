/**
 * Benchmark Chart - Visual score comparison with CSS-based bars
 */

'use client';

import React, { useState } from 'react';
import { RankingEntry } from '@/types';

interface BenchmarkChartProps {
  seoRankings: RankingEntry[];
  aeoRankings: RankingEntry[];
  marketAverage: {
    seo: number;
    aeo: number;
  };
}

type MetricView = 'seo' | 'aeo' | 'both';

export function BenchmarkChart({
  seoRankings,
  aeoRankings,
  marketAverage,
}: BenchmarkChartProps) {
  const [view, setView] = useState<MetricView>('both');

  const getBarColor = (score: number): string => {
    if (score >= 80) return 'bg-gradient-to-r from-success-400 to-success-600';
    if (score >= 60) return 'bg-gradient-to-r from-warning-400 to-warning-600';
    return 'bg-gradient-to-r from-danger-400 to-danger-600';
  };

  const renderBar = (
    label: string,
    url: string,
    score: number,
    average: number,
    rank: number
  ) => {
    const isAboveAverage = score >= average;

    return (
      <div key={url} className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <span className="text-xs font-semibold text-gray-500 flex-shrink-0">
              #{rank}
            </span>
            <span className="text-sm font-medium text-gray-900 truncate">
              {label || url}
            </span>
          </div>
          <span className="text-sm font-bold text-gray-900 ml-2">
            {Math.round(score)}
          </span>
        </div>

        <div className="relative h-8 bg-gray-100 rounded-lg overflow-hidden">
          {/* Average Line */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-gray-400 z-10"
            style={{ left: `${average}%` }}
            title={`Market Average: ${Math.round(average)}`}
          >
            <div className="absolute -top-1 -left-1.5 w-3 h-3 bg-gray-400 rounded-full" />
          </div>

          {/* Score Bar */}
          <div
            className={`h-full ${getBarColor(score)} transition-all duration-500 ease-out flex items-center justify-end pr-2`}
            style={{ width: `${score}%` }}
          >
            <span className="text-white text-xs font-semibold drop-shadow">
              {Math.round(score)}
            </span>
          </div>
        </div>

        {/* Delta Info */}
        <div className="flex items-center justify-between mt-1 text-xs">
          <span className={isAboveAverage ? 'text-success-600' : 'text-danger-600'}>
            {isAboveAverage ? '▲' : '▼'} {Math.abs(score - average).toFixed(1)} from avg
          </span>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:underline truncate max-w-[200px]"
          >
            {url}
          </a>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Performance Benchmark</h2>

        {/* View Toggle */}
        <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setView('seo')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
              view === 'seo'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            SEO
          </button>
          <button
            onClick={() => setView('aeo')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
              view === 'aeo'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            AEO
          </button>
          <button
            onClick={() => setView('both')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
              view === 'both'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Both
          </button>
        </div>
      </div>

      {/* SEO Chart */}
      {(view === 'seo' || view === 'both') && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">SEO Scores</h3>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <div className="w-0.5 h-4 bg-gray-400" />
              <span>Avg: {Math.round(marketAverage.seo)}</span>
            </div>
          </div>
          <div>
            {seoRankings.map((entry) =>
              renderBar(
                entry.label || '',
                entry.url,
                entry.score,
                marketAverage.seo,
                entry.rank
              )
            )}
          </div>
        </div>
      )}

      {/* AEO Chart */}
      {(view === 'aeo' || view === 'both') && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">AEO Scores</h3>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <div className="w-0.5 h-4 bg-gray-400" />
              <span>Avg: {Math.round(marketAverage.aeo)}</span>
            </div>
          </div>
          <div>
            {aeoRankings.map((entry) =>
              renderBar(
                entry.label || '',
                entry.url,
                entry.score,
                marketAverage.aeo,
                entry.rank
              )
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-8 h-3 bg-gradient-to-r from-success-400 to-success-600 rounded" />
            <span>80-100 (Excellent)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-3 bg-gradient-to-r from-warning-400 to-warning-600 rounded" />
            <span>60-79 (Good)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-3 bg-gradient-to-r from-danger-400 to-danger-600 rounded" />
            <span>0-59 (Needs Improvement)</span>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <div className="w-0.5 h-4 bg-gray-400" />
            <span>Market Average</span>
          </div>
        </div>
      </div>
    </div>
  );
}
