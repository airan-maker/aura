/**
 * Comparison Grid - Responsive grid of competitor cards
 */

'use client';

import React from 'react';
import { CompetitorCard } from './CompetitorCard';
import { RankingEntry } from '@/types';

interface ComparisonGridProps {
  seoRankings: RankingEntry[];
  aeoRankings: RankingEntry[];
  marketAverage: {
    seo: number;
    aeo: number;
  };
}

export function ComparisonGrid({
  seoRankings,
  aeoRankings,
  marketAverage,
}: ComparisonGridProps) {
  // Create combined competitor data
  const competitors = seoRankings.map((seoEntry) => {
    const aeoEntry = aeoRankings.find((a) => a.url === seoEntry.url);

    return {
      url: seoEntry.url,
      label: seoEntry.label,
      seoScore: seoEntry.score,
      aeoScore: aeoEntry?.score || 0,
      seoRank: seoEntry.rank,
      aeoRank: aeoEntry?.rank || 0,
      deltaFromLeader: {
        seo: seoEntry.delta_from_leader,
        aeo: aeoEntry?.delta_from_leader || 0,
      },
      isLeader: seoEntry.rank === 1 && aeoEntry?.rank === 1,
      isAboveAverage:
        seoEntry.score >= marketAverage.seo &&
        (aeoEntry?.score || 0) >= marketAverage.aeo,
    };
  });

  return (
    <div>
      {/* Grid Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Competitive Comparison
        </h2>
        <p className="text-gray-600">
          Side-by-side analysis of {competitors.length} competitors
        </p>
      </div>

      {/* Market Averages */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Market Averages</span>
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-600">SEO:</span>
              <span className="font-semibold text-gray-900">{Math.round(marketAverage.seo)}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">AEO:</span>
              <span className="font-semibold text-gray-900">{Math.round(marketAverage.aeo)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Competitor Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {competitors.map((competitor, index) => (
          <CompetitorCard
            key={competitor.url}
            url={competitor.url}
            label={competitor.label}
            seoScore={competitor.seoScore}
            aeoScore={competitor.aeoScore}
            seoRank={competitor.seoRank}
            aeoRank={competitor.aeoRank}
            deltaFromLeader={competitor.deltaFromLeader}
            isLeader={competitor.isLeader}
            isAboveAverage={competitor.isAboveAverage}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Legend</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 border-yellow-400" />
            <span className="text-gray-700">Market Leader</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-success-200 bg-white" />
            <span className="text-gray-700">Above Average</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-100 border border-yellow-200" />
            <span className="text-gray-700">Rank #1</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-100 border border-gray-200" />
            <span className="text-gray-700">Rank #2</span>
          </div>
        </div>
      </div>
    </div>
  );
}
