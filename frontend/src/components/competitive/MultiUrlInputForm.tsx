/**
 * Multi-URL Input Form for Competitive Analysis
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface UrlEntry {
  id: string;
  url: string;
  label: string;
}

interface MultiUrlInputFormProps {
  onSubmit: (urls: string[], labels: string[], name?: string) => Promise<void>;
  loading?: boolean;
}

export function MultiUrlInputForm({ onSubmit, loading = false }: MultiUrlInputFormProps) {
  const [batchName, setBatchName] = useState('');
  const [urlEntries, setUrlEntries] = useState<UrlEntry[]>([
    { id: '1', url: '', label: '' },
    { id: '2', url: '', label: '' },
  ]);
  const [error, setError] = useState('');

  const validateUrl = (input: string): boolean => {
    try {
      const urlObj = new URL(input);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleAddUrl = () => {
    if (urlEntries.length >= 5) {
      setError('Maximum 5 URLs allowed');
      return;
    }
    setUrlEntries([
      ...urlEntries,
      { id: Date.now().toString(), url: '', label: '' },
    ]);
    setError('');
  };

  const handleRemoveUrl = (id: string) => {
    if (urlEntries.length <= 2) {
      setError('Minimum 2 URLs required');
      return;
    }
    setUrlEntries(urlEntries.filter((entry) => entry.id !== id));
    setError('');
  };

  const handleUrlChange = (id: string, url: string) => {
    setUrlEntries(
      urlEntries.map((entry) =>
        entry.id === id ? { ...entry, url } : entry
      )
    );
  };

  const handleLabelChange = (id: string, label: string) => {
    setUrlEntries(
      urlEntries.map((entry) =>
        entry.id === id ? { ...entry, label } : entry
      )
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate all URLs are filled
    const urls = urlEntries.map((entry) => entry.url.trim()).filter(Boolean);
    if (urls.length < 2) {
      setError('Please enter at least 2 URLs');
      return;
    }

    // Validate URL format
    for (const url of urls) {
      if (!validateUrl(url)) {
        setError(`Invalid URL format: ${url}`);
        return;
      }
    }

    // Check for duplicates
    const uniqueUrls = new Set(urls);
    if (uniqueUrls.size !== urls.length) {
      setError('Duplicate URLs are not allowed');
      return;
    }

    // Get labels (only for filled URLs)
    const labels = urlEntries
      .filter((entry) => entry.url.trim())
      .map((entry) => entry.label.trim())
      .filter(Boolean);

    try {
      await onSubmit(
        urls,
        labels.length === urls.length ? labels : [],
        batchName.trim() || undefined
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit analysis');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl">
      {/* Batch Name */}
      <div className="mb-6">
        <label htmlFor="batch-name" className="block text-sm font-medium text-gray-700 mb-2">
          Analysis Name (Optional)
        </label>
        <input
          id="batch-name"
          type="text"
          value={batchName}
          onChange={(e) => setBatchName(e.target.value)}
          placeholder="Q1 2025 Competitor Analysis"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition"
          disabled={loading}
          maxLength={255}
        />
      </div>

      {/* URL Entries */}
      <div className="space-y-4 mb-4">
        {urlEntries.map((entry, index) => (
          <div key={entry.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-semibold text-sm">
                {index + 1}
              </div>
              <div className="flex-1 space-y-3">
                {/* URL Input */}
                <div>
                  <label htmlFor={`url-${entry.id}`} className="block text-xs font-medium text-gray-600 mb-1">
                    Website URL *
                  </label>
                  <input
                    id={`url-${entry.id}`}
                    type="text"
                    value={entry.url}
                    onChange={(e) => handleUrlChange(entry.id, e.target.value)}
                    placeholder="https://competitor.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition text-sm"
                    disabled={loading}
                  />
                </div>

                {/* Label Input */}
                <div>
                  <label htmlFor={`label-${entry.id}`} className="block text-xs font-medium text-gray-600 mb-1">
                    Label (Optional)
                  </label>
                  <input
                    id={`label-${entry.id}`}
                    type="text"
                    value={entry.label}
                    onChange={(e) => handleLabelChange(entry.id, e.target.value)}
                    placeholder={`Competitor ${String.fromCharCode(65 + index)}`}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition text-sm"
                    disabled={loading}
                    maxLength={255}
                  />
                </div>
              </div>

              {/* Remove Button */}
              {urlEntries.length > 2 && (
                <button
                  type="button"
                  onClick={() => handleRemoveUrl(entry.id)}
                  disabled={loading}
                  className="flex-shrink-0 text-danger-600 hover:text-danger-700 disabled:opacity-50 disabled:cursor-not-allowed transition p-1"
                  title="Remove URL"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add URL Button */}
      {urlEntries.length < 5 && (
        <button
          type="button"
          onClick={handleAddUrl}
          disabled={loading}
          className="w-full mb-6 px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-primary-500 hover:text-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Another URL ({urlEntries.length}/5)
        </button>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-lg">
          <p className="text-sm text-danger-700">{error}</p>
        </div>
      )}

      {/* Submit Button */}
      <Button type="submit" loading={loading} size="lg" className="w-full">
        {loading ? 'Starting Analysis...' : `Analyze ${urlEntries.filter(e => e.url.trim()).length} Competitors`}
      </Button>

      {/* Info Text */}
      <p className="mt-4 text-xs text-gray-500 text-center">
        * Enter 2-5 competitor URLs to compare. Labels are optional but help identify each site in the results.
      </p>
    </form>
  );
}
