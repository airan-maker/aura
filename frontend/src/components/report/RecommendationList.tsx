/**
 * Recommendations list component
 */

'use client';

import React, { useState } from 'react';
import { Recommendation } from '@/types';
import { Card } from '@/components/ui/Card';

interface RecommendationListProps {
  recommendations: Recommendation[];
}

export function RecommendationList({ recommendations }: RecommendationListProps) {
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const filteredRecommendations = recommendations.filter(rec => {
    if (filter === 'all') return true;
    return rec.priority === filter;
  });

  const getPriorityBadge = (priority: string) => {
    const styles = {
      high: 'bg-danger-100 text-danger-800 border-danger-200',
      medium: 'bg-warning-100 text-warning-800 border-warning-200',
      low: 'bg-primary-100 text-primary-800 border-primary-200',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${styles[priority as keyof typeof styles]}`}>
        {priority.toUpperCase()}
      </span>
    );
  };

  const getCategoryIcon = (category: string) => {
    if (category === 'seo') {
      return (
        <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    );
  };

  const highCount = recommendations.filter(r => r.priority === 'high').length;
  const mediumCount = recommendations.filter(r => r.priority === 'medium').length;
  const lowCount = recommendations.filter(r => r.priority === 'low').length;

  return (
    <Card title="Recommendations">
      {/* Filter buttons */}
      <div className="flex gap-2 mb-6 flex-wrap">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            filter === 'all'
              ? 'bg-gray-900 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All ({recommendations.length})
        </button>
        <button
          onClick={() => setFilter('high')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            filter === 'high'
              ? 'bg-danger-600 text-white'
              : 'bg-danger-50 text-danger-700 hover:bg-danger-100'
          }`}
        >
          High Priority ({highCount})
        </button>
        <button
          onClick={() => setFilter('medium')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            filter === 'medium'
              ? 'bg-warning-600 text-white'
              : 'bg-warning-50 text-warning-700 hover:bg-warning-100'
          }`}
        >
          Medium ({mediumCount})
        </button>
        <button
          onClick={() => setFilter('low')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            filter === 'low'
              ? 'bg-primary-600 text-white'
              : 'bg-primary-50 text-primary-700 hover:bg-primary-100'
          }`}
        >
          Low ({lowCount})
        </button>
      </div>

      {/* Recommendations list */}
      <div className="space-y-4">
        {filteredRecommendations.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No recommendations in this category</p>
        ) : (
          filteredRecommendations.map((rec, idx) => (
            <div
              key={idx}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getCategoryIcon(rec.category)}
                  <h4 className="font-medium text-gray-900">{rec.title}</h4>
                </div>
                {getPriorityBadge(rec.priority)}
              </div>
              <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
              <div className="flex items-center text-xs text-gray-500">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Impact: {rec.impact}
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
