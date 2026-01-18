/**
 * Competitive Analysis - Multi-URL Input Page
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MultiUrlInputForm } from '@/components/competitive/MultiUrlInputForm';
import { createCompetitiveAnalysis } from '@/lib/api-client';

export default function CompetitivePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (urls: string[], labels: string[], name?: string) => {
    setLoading(true);
    try {
      const batch = await createCompetitiveAnalysis({
        urls,
        labels: labels.length > 0 ? labels : undefined,
        name,
      });
      // Redirect to batch progress page
      router.push(`/competitive/${batch.id}`);
    } catch (error) {
      console.error('Failed to create competitive analysis:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)]">
      {/* Hero Section */}
      <div className="text-center mb-12 max-w-4xl">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Competitive{' '}
          <span className="text-primary-600">Analysis</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Compare 2-5 competitor websites side-by-side. Get AI-powered insights on market positioning,
          identify opportunities, and discover competitive threats.
        </p>
      </div>

      {/* Input Form */}
      <MultiUrlInputForm onSubmit={handleSubmit} loading={loading} />

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-8 mt-16 max-w-5xl">
        <div className="text-center">
          <div className="bg-primary-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Side-by-Side Rankings</h3>
          <p className="text-sm text-gray-600">
            Compare SEO and AEO scores across all competitors with detailed rankings and performance gaps
          </p>
        </div>

        <div className="text-center">
          <div className="bg-purple-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">AI-Powered Insights</h3>
          <p className="text-sm text-gray-600">
            Get intelligent analysis of competitive landscape with actionable opportunities and threat identification
          </p>
        </div>

        <div className="text-center">
          <div className="bg-success-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Market Benchmarking</h3>
          <p className="text-sm text-gray-600">
            Identify market leaders, understand average performance, and find your competitive position
          </p>
        </div>
      </div>

      {/* Single Analysis Link */}
      <div className="mt-12 text-center">
        <p className="text-sm text-gray-500">
          Need to analyze a single website?{' '}
          <a href="/" className="text-primary-600 hover:underline font-medium">
            Go to single-site analysis
          </a>
        </p>
      </div>
    </div>
  );
}
