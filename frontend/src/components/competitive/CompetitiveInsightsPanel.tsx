/**
 * Competitive Insights Panel - AI-generated insights, opportunities, and threats
 */

'use client';

import React from 'react';

interface CompetitiveInsightsPanelProps {
  insights: string;
  opportunities: string[];
  threats: string[];
}

export function CompetitiveInsightsPanel({
  insights,
  opportunities,
  threats,
}: CompetitiveInsightsPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        AI-Powered Insights
      </h2>

      {/* Insights Overview */}
      <div className="mb-8">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Competitive Landscape
            </h3>
            <p className="text-gray-700 leading-relaxed">{insights}</p>
          </div>
        </div>
      </div>

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Opportunities */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-success-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Opportunities</h3>
          </div>
          <ul className="space-y-3">
            {opportunities.length > 0 ? (
              opportunities.map((opportunity, index) => (
                <li key={index} className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">{opportunity}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-gray-500 italic">No specific opportunities identified</li>
            )}
          </ul>
        </div>

        {/* Threats */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-warning-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Threats</h3>
          </div>
          <ul className="space-y-3">
            {threats.length > 0 ? (
              threats.map((threat, index) => (
                <li key={index} className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">{threat}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-gray-500 italic">No significant threats identified</li>
            )}
          </ul>
        </div>

        {/* Key Metrics */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Action Items</h3>
          </div>
          <div className="space-y-3">
            <div className="p-3 bg-primary-50 border border-primary-200 rounded-lg">
              <p className="text-xs font-semibold text-primary-900 mb-1">Priority Focus</p>
              <p className="text-sm text-primary-700">
                {opportunities.length > 0
                  ? opportunities[0]
                  : 'Maintain current positioning and monitor competitors'}
              </p>
            </div>
            <div className="p-3 bg-warning-50 border border-warning-200 rounded-lg">
              <p className="text-xs font-semibold text-warning-900 mb-1">Watch Out For</p>
              <p className="text-sm text-warning-700">
                {threats.length > 0
                  ? threats[0]
                  : 'Keep monitoring market changes'}
              </p>
            </div>
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-xs font-semibold text-gray-900 mb-1">Next Steps</p>
              <p className="text-sm text-gray-700">
                Review individual competitor details and implement top opportunities
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
