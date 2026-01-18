/**
 * Type definitions for Aura API
 */

export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface AnalysisRequest {
  id: string;
  url: string;
  status: AnalysisStatus;
  progress: number;
  current_step?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface MetaTagsAnalysis {
  title_present: boolean;
  title_length: number;
  description_present: boolean;
  description_length: number;
  og_tags_present: boolean;
  score: number;
  issues: string[];
}

export interface HeadingAnalysis {
  h1_count: number;
  h1_text?: string;
  heading_hierarchy_valid: boolean;
  score: number;
  issues: string[];
}

export interface PerformanceAnalysis {
  load_time: number;
  score: number;
  issues: string[];
}

export interface MobileAnalysis {
  viewport_tag_present: boolean;
  score: number;
  issues: string[];
}

export interface SecurityAnalysis {
  https: boolean;
  score: number;
  issues: string[];
}

export interface StructuredDataAnalysis {
  present: boolean;
  types: string[];
  score: number;
  issues: string[];
}

export interface SEOMetrics {
  meta_tags: MetaTagsAnalysis;
  headings: HeadingAnalysis;
  performance: PerformanceAnalysis;
  mobile: MobileAnalysis;
  security: SecurityAnalysis;
  structured_data: StructuredDataAnalysis;
}

export interface AEOMetrics {
  what_it_does: string;
  products_services: string;
  target_audience: string;
  unique_value: string;
  clarity_score: number;
  overall_impression: string;
}

export interface Recommendation {
  category: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: string;
}

export interface AnalysisResult {
  id: string;
  request_id: string;
  url: string;
  seo_score: number;
  seo_metrics: SEOMetrics;
  aeo_score: number;
  aeo_metrics: AEOMetrics;
  recommendations: Recommendation[];
  analysis_duration: number;
  created_at: string;
}

export interface WebSocketMessage {
  type: 'progress' | 'completed' | 'error' | 'pong';
  progress?: number;
  step?: string;
  status?: AnalysisStatus;
  error?: string;
}

// Competitive Analysis Types

export interface CompetitiveURLStatus {
  url: string;
  label?: string;
  status: AnalysisStatus;
  progress: number;
  request_id: string;
  is_primary: boolean;
  order_index: number;
}

export interface CompetitiveBatch {
  id: string;
  name?: string;
  status: AnalysisStatus;
  progress: number;
  total_urls: number;
  completed_count: number;
  failed_count: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  urls: CompetitiveURLStatus[];
}

export interface RankingEntry {
  url: string;
  label?: string;
  score: number;
  rank: number;
  delta_from_leader: number;
  delta_from_average: number;
}

export interface ComparisonData {
  seo_rankings: RankingEntry[];
  aeo_rankings: RankingEntry[];
  market_leader: {
    seo: { url: string; score: number; label?: string };
    aeo: { url: string; score: number; label?: string };
  };
  market_average: {
    seo: number;
    aeo: number;
  };
  insights: string;
  opportunities: string[];
  threats: string[];
}

export interface CompetitiveResult {
  batch: CompetitiveBatch;
  individual_results: Array<{
    url: string;
    label?: string;
    seo_score: number;
    aeo_score: number;
    seo_metrics: any;
    aeo_metrics: any;
    recommendations: Recommendation[];
  }>;
  comparison: ComparisonData;
}

export interface CompetitiveBatchWebSocketMessage {
  status?: AnalysisStatus;
  progress?: number;
  current_url?: number;
  total_urls?: number;
  current_step?: string;
  completed_count?: number;
  failed_count?: number;
  individual_statuses?: Record<string, {
    progress: number;
    step: string;
    status: AnalysisStatus;
  }>;
  comparison_id?: string;
  error?: string;
}
