/**
 * URL Input Form component for analysis submission
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface UrlInputFormProps {
  onSubmit: (url: string) => Promise<void>;
  loading?: boolean;
}

export function UrlInputForm({ onSubmit, loading = false }: UrlInputFormProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validateUrl = (input: string): boolean => {
    try {
      const urlObj = new URL(input);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (!validateUrl(url)) {
      setError('Please enter a valid HTTP or HTTPS URL');
      return;
    }

    try {
      await onSubmit(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit analysis');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl">
      <div className="mb-4">
        <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
          Website URL
        </label>
        <input
          id="url"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition"
          disabled={loading}
        />
        {error && (
          <p className="mt-2 text-sm text-danger-600">{error}</p>
        )}
      </div>
      <Button type="submit" loading={loading} size="lg" className="w-full">
        {loading ? 'Analyzing...' : 'Analyze Website'}
      </Button>
    </form>
  );
}
