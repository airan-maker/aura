/**
 * API Client for Aura Backend
 */

import {
  AnalysisRequest,
  AnalysisResult,
  CompetitiveBatch,
  ComparisonData,
  CompetitiveResult
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string, public details?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Create a new analysis request
 */
export async function createAnalysis(url: string): Promise<AnalysisRequest> {
  return fetchApi<AnalysisRequest>('/analysis', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

/**
 * Get analysis status
 */
export async function getAnalysisStatus(requestId: string): Promise<AnalysisRequest> {
  return fetchApi<AnalysisRequest>(`/analysis/${requestId}`);
}

/**
 * Get analysis results
 */
export async function getAnalysisResults(requestId: string): Promise<AnalysisResult> {
  return fetchApi<AnalysisResult>(`/analysis/${requestId}/results`);
}

/**
 * List all analyses
 */
export async function listAnalyses(skip: number = 0, limit: number = 10): Promise<AnalysisRequest[]> {
  return fetchApi<AnalysisRequest[]>(`/analysis?skip=${skip}&limit=${limit}`);
}

/**
 * Create WebSocket connection for real-time updates
 */
export function createWebSocket(requestId: string): WebSocket {
  const wsUrl = API_BASE_URL.replace(/^http/, 'ws');
  return new WebSocket(`${wsUrl}/analysis/${requestId}/ws`);
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/health');
}

// Competitive Analysis API

export interface CompetitiveAnalysisCreateData {
  urls: string[];
  labels?: string[];
  name?: string;
}

/**
 * Create a new competitive analysis batch
 */
export async function createCompetitiveAnalysis(
  data: CompetitiveAnalysisCreateData
): Promise<CompetitiveBatch> {
  return fetchApi<CompetitiveBatch>('/competitive', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get competitive analysis batch status
 */
export async function getCompetitiveBatchStatus(
  batchId: string
): Promise<CompetitiveBatch> {
  return fetchApi<CompetitiveBatch>(`/competitive/${batchId}`);
}

/**
 * Get complete competitive analysis results
 */
export async function getCompetitiveResults(
  batchId: string
): Promise<CompetitiveResult> {
  return fetchApi<CompetitiveResult>(`/competitive/${batchId}/results`);
}

/**
 * Get comparison data only
 */
export async function getComparisonData(
  batchId: string
): Promise<ComparisonData> {
  return fetchApi<ComparisonData>(`/competitive/${batchId}/comparison`);
}

/**
 * Create WebSocket connection for competitive batch real-time updates
 */
export function createCompetitiveWebSocket(batchId: string): WebSocket {
  const wsUrl = API_BASE_URL.replace(/^http/, 'ws');
  return new WebSocket(`${wsUrl}/competitive/${batchId}/ws`);
}

export { ApiError };
