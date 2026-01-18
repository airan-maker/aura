/**
 * Home page - URL Input Form
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UrlInputForm } from '@/components/analysis/UrlInputForm';
import { createAnalysis } from '@/lib/api-client';

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (url: string) => {
    setLoading(true);
    try {
      const analysis = await createAnalysis(url);
      // Redirect to analysis progress page
      router.push(`/analysis/${analysis.id}`);
    } catch (error) {
      console.error('Failed to create analysis:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)]">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Optimize for Search &{' '}
          <span className="text-primary-600">AI Engines</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Analyze your website's SEO performance and AI Engine Optimization (AEO) readiness
          to ensure you're visible in both Google search and AI assistants like ChatGPT.
        </p>
      </div>

      {/* Input Form */}
      <UrlInputForm onSubmit={handleSubmit} loading={loading} />

      {/* Competitive Analysis Link */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Want to compare multiple competitors?{' '}
          <a href="/competitive" className="text-primary-600 hover:underline font-medium">
            Try Competitive Analysis
          </a>
        </p>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-8 mt-16 max-w-5xl">
        <div className="text-center">
          <div className="bg-primary-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">SEO Analysis</h3>
          <p className="text-sm text-gray-600">
            Comprehensive analysis of meta tags, performance, mobile optimization, and more
          </p>
        </div>

        <div className="text-center">
          <div className="bg-purple-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">AEO Insights</h3>
          <p className="text-sm text-gray-600">
            AI-powered analysis of how well your brand communicates its value proposition
          </p>
        </div>

        <div className="text-center">
          <div className="bg-success-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Actionable Recommendations</h3>
          <p className="text-sm text-gray-600">
            Priority-based recommendations to improve your visibility in search and AI
          </p>
        </div>
      </div>
    </div>
  );
}
