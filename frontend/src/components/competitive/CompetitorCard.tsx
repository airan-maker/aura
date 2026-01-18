/**
 * Competitor Card - Individual competitor summary with rank badges
 */

'use client';

import React from 'react';

interface CompetitorCardProps {
  url: string;
  label?: string;
  seoScore: number;
  aeoScore: number;
  seoRank: number;
  aeoRank: number;
  deltaFromLeader: {
    seo: number;
    aeo: number;
  };
  isLeader?: boolean;
  isAboveAverage?: boolean;
}

export function CompetitorCard({
  url,
  label,
  seoScore,
  aeoScore,
  seoRank,
  aeoRank,
  deltaFromLeader,
  isLeader = false,
  isAboveAverage = true,
}: CompetitorCardProps) {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-success-600';
    if (score >= 60) return 'text-warning-600';
    return 'text-danger-600';
  };

  const getScoreBgColor = (score: number): string => {
    if (score >= 80) return 'bg-success-50';
    if (score >= 60) return 'bg-warning-50';
    return 'bg-danger-50';
  };

  const getRankBadgeColor = (rank: number): string => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (rank === 2) return 'bg-gray-100 text-gray-800 border-gray-200';
    if (rank === 3) return 'bg-orange-100 text-orange-800 border-orange-200';
    return 'bg-gray-50 text-gray-600 border-gray-200';
  };

  const borderColor = isLeader
    ? 'border-yellow-400 border-2'
    : isAboveAverage
    ? 'border-success-200'
    : 'border-gray-200';

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 border ${borderColor} transition-all hover:shadow-lg`}>
      {/* Leader Badge */}
      {isLeader && (
        <div className="mb-4 flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-yellow-100 text-yellow-800 px-3 py-1.5 rounded-full text-xs font-semibold border border-yellow-200">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Market Leader
          </div>
        </div>
      )}

      {/* URL and Label */}
      <div className="mb-4">
        {label && (
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{label}</h3>
        )}
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary-600 hover:underline break-all"
        >
          {url}
        </a>
      </div>

      {/* Scores */}
      <div className="space-y-3 mb-4">
        {/* SEO Score */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">SEO Score</span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${getRankBadgeColor(seoRank)}`}>
              #{seoRank}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className={`text-2xl font-bold ${getScoreColor(seoScore)}`}>
              {Math.round(seoScore)}
            </div>
            <div className={`flex-1 h-2 rounded-full ${getScoreBgColor(seoScore)}`}>
              <div
                className={`h-2 rounded-full transition-all ${getScoreColor(seoScore).replace('text-', 'bg-')}`}
                style={{ width: `${seoScore}%` }}
              />
            </div>
          </div>
          {deltaFromLeader.seo !== 0 && (
            <p className="text-xs text-gray-500 mt-1">
              {deltaFromLeader.seo > 0 ? '+' : ''}{deltaFromLeader.seo.toFixed(1)} from leader
            </p>
          )}
        </div>

        {/* AEO Score */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">AEO Score</span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${getRankBadgeColor(aeoRank)}`}>
              #{aeoRank}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className={`text-2xl font-bold ${getScoreColor(aeoScore)}`}>
              {Math.round(aeoScore)}
            </div>
            <div className={`flex-1 h-2 rounded-full ${getScoreBgColor(aeoScore)}`}>
              <div
                className={`h-2 rounded-full transition-all ${getScoreColor(aeoScore).replace('text-', 'bg-')}`}
                style={{ width: `${aeoScore}%` }}
              />
            </div>
          </div>
          {deltaFromLeader.aeo !== 0 && (
            <p className="text-xs text-gray-500 mt-1">
              {deltaFromLeader.aeo > 0 ? '+' : ''}{deltaFromLeader.aeo.toFixed(1)} from leader
            </p>
          )}
        </div>
      </div>

      {/* Overall Performance Indicator */}
      <div className="pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Overall</span>
          <span className={`font-semibold ${getScoreColor((seoScore + aeoScore) / 2)}`}>
            {Math.round((seoScore + aeoScore) / 2)}/100
          </span>
        </div>
      </div>
    </div>
  );
}
