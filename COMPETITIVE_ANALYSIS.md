# Competitive Analysis Feature Documentation

## Overview

Aura's Competitive Analysis feature allows you to compare 2-5 competitor websites side-by-side, providing AI-powered insights on market positioning, opportunities, and competitive threats.

## Features

### 1. Multi-URL Batch Analysis
- **Concurrent Processing**: Analyze 2-5 URLs simultaneously with intelligent concurrency control
- **Real-time Progress**: WebSocket-based live updates for batch and individual URL progress
- **Smart Labeling**: Optional custom labels for each competitor (e.g., "Competitor A", "Our Site")
- **Batch Naming**: Organize analyses with custom names (e.g., "Q1 2025 Analysis")

### 2. Side-by-Side Comparison
- **SEO & AEO Rankings**: Automatic ranking of all competitors by SEO and AEO scores
- **Market Benchmarking**: Identify market leaders and calculate market averages
- **Performance Gaps**: Visual indicators showing distance from leader and average
- **Responsive Grid**: Adapts from 1-4 columns based on screen size

### 3. AI-Powered Insights
- **Competitive Landscape Overview**: AI-generated summary of market dynamics
- **Opportunity Identification**: Top 5 actionable opportunities based on competitive gaps
- **Threat Analysis**: Top 3 competitive risks and advantages of leaders
- **Prioritized Action Items**: Ranked next steps for immediate implementation

### 4. Visual Analytics
- **Benchmark Chart**: Horizontal bar charts with gradient color coding
- **Market Average Line**: Visual reference for performance benchmarking
- **Rank Badges**: Gold (#1), Silver (#2), Bronze (#3) rankings
- **Score Gauges**: Color-coded progress bars (green/yellow/red)

## User Guide

### Starting a Competitive Analysis

1. Navigate to `/competitive` in your browser
2. Enter 2-5 competitor URLs
3. (Optional) Add labels for each URL to identify them easily
4. (Optional) Name your analysis for future reference
5. Click "Analyze Competitors"

### Viewing Progress

The progress page (`/competitive/[batchId]`) shows:
- **Overall Progress**: Aggregate completion percentage
- **Individual Status**: Per-URL progress with status icons
  - ✅ Completed (green)
  - ❌ Failed (red)
  - 🔄 Processing (animated spinner)
  - ⏳ Pending (gray clock)
- **Real-time Updates**: WebSocket connection indicator

### Understanding Results

The results page (`/competitive/[batchId]/results`) contains:

#### Summary Stats
- Total competitors analyzed
- SEO leader score
- AEO leader score
- Number of opportunities identified

#### AI-Powered Insights Panel
- **Competitive Landscape**: 3-5 sentence overview of market dynamics
- **Opportunities Column**: Top 5 improvement opportunities with ✅ icons
- **Threats Column**: Top 3 competitive risks with ⚠️ icons
- **Action Items**: Prioritized next steps

#### Benchmark Chart
- Toggle between SEO, AEO, or Both views
- Horizontal bars with gradient fills
- Market average line for context
- Delta indicators (▲ above average, ▼ below average)

#### Comparison Grid
- **Market Leader Badge**: Gold badge for overall winner
- **Rank Badges**: #1 (gold), #2 (silver), #3 (bronze)
- **Score Displays**: Large, color-coded scores with progress bars
- **Delta from Leader**: Shows point difference from top performer

## API Reference

### Create Competitive Analysis

**Endpoint:** `POST /api/v1/competitive`

**Request Body:**
```json
{
  "urls": [
    "https://competitor1.com",
    "https://competitor2.com",
    "https://competitor3.com"
  ],
  "labels": ["Competitor A", "Competitor B", "Competitor C"],
  "name": "Q1 2025 Analysis"
}
```

**Validation:**
- `urls`: Array of 2-5 valid HTTP/HTTPS URLs (required)
- `labels`: Array matching URL count (optional)
- `name`: String up to 255 characters (optional)

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Q1 2025 Analysis",
  "status": "pending",
  "progress": 0,
  "total_urls": 3,
  "completed_count": 0,
  "failed_count": 0,
  "created_at": "2025-01-17T10:00:00Z",
  "urls": [
    {
      "url": "https://competitor1.com",
      "label": "Competitor A",
      "status": "pending",
      "progress": 0,
      "request_id": "uuid",
      "is_primary": true,
      "order_index": 0
    }
  ]
}
```

### Get Batch Status

**Endpoint:** `GET /api/v1/competitive/{batch_id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Q1 2025 Analysis",
  "status": "processing",
  "progress": 67,
  "total_urls": 3,
  "completed_count": 2,
  "failed_count": 0,
  "created_at": "2025-01-17T10:00:00Z",
  "started_at": "2025-01-17T10:00:05Z",
  "urls": [...]
}
```

### Get Complete Results

**Endpoint:** `GET /api/v1/competitive/{batch_id}/results`

**Response (200 OK):**
```json
{
  "batch": {...},
  "individual_results": [
    {
      "url": "https://competitor1.com",
      "label": "Competitor A",
      "seo_score": 85.5,
      "aeo_score": 78.3,
      "seo_metrics": {...},
      "aeo_metrics": {...},
      "recommendations": [...]
    }
  ],
  "comparison": {
    "seo_rankings": [
      {
        "url": "https://competitor1.com",
        "label": "Competitor A",
        "score": 85.5,
        "rank": 1,
        "delta_from_leader": 0.0,
        "delta_from_average": 5.5
      }
    ],
    "aeo_rankings": [...],
    "market_leader": {
      "seo": {"url": "...", "score": 85.5, "label": "..."},
      "aeo": {"url": "...", "score": 82.1, "label": "..."}
    },
    "market_average": {
      "seo": 80.0,
      "aeo": 75.3
    },
    "insights": "AI-generated competitive landscape overview...",
    "opportunities": [
      "Add structured data - only 1/3 competitors have it",
      "Improve page speed to beat market average"
    ],
    "threats": [
      "Competitor A has significantly faster load times",
      "Two competitors have better mobile optimization"
    ]
  }
}
```

### Get Comparison Only

**Endpoint:** `GET /api/v1/competitive/{batch_id}/comparison`

**Response (200 OK):**
Returns only the `comparison` object from the complete results.

### WebSocket Real-time Updates

**Endpoint:** `WS /api/v1/competitive/{batch_id}/ws`

**Message Format:**
```json
{
  "status": "processing",
  "progress": 45,
  "current_url": 2,
  "total_urls": 3,
  "current_step": "URL 2/3: Analyzing SEO",
  "completed_count": 1,
  "failed_count": 0,
  "individual_statuses": {
    "request-uuid-1": {
      "progress": 100,
      "step": "Completed",
      "status": "completed"
    },
    "request-uuid-2": {
      "progress": 60,
      "step": "Analyzing AEO",
      "status": "processing"
    }
  }
}
```

## Technical Architecture

### Backend Components

#### 1. CompetitiveOrchestrator
- **Purpose**: Manages batch analysis with concurrency control
- **Concurrency**: `asyncio.Semaphore(3)` limits parallel crawlers
- **Progress Aggregation**: Combines individual URL progress into batch progress
- **Error Handling**: Marks batch as completed if ≥2 URLs succeed

#### 2. ComparisonService
- **Ranking Calculation**: Sorts competitors by SEO/AEO scores
- **Benchmarking**: Identifies leaders, laggards, and market averages
- **Data Preparation**: Formats competitor data for LLM analysis

#### 3. BatchLLMAnalyzer
- **Cost Optimization**: Single GPT-4 call for all competitors (80% savings)
- **Token Budget**: ~750 tokens per competitor (supports up to 5)
- **Output**: Insights, opportunities, threats, and overall winner

### Frontend Components

#### 1. MultiUrlInputForm
- Dynamic URL fields (add/remove)
- Real-time validation
- Label and name inputs

#### 2. BatchProgressTracker
- Overall progress bar
- Individual URL status indicators
- WebSocket connection status

#### 3. ComparisonGrid
- Responsive grid layout (1-4 columns)
- CompetitorCard components
- Market average display

#### 4. CompetitiveInsightsPanel
- 3-column layout (Opportunities, Threats, Actions)
- AI-generated insights overview
- Priority action cards

#### 5. BenchmarkChart
- CSS-based horizontal bars
- View toggle (SEO/AEO/Both)
- Market average line overlay

## Performance Considerations

### Concurrency Strategy
- **Max Concurrent Crawlers**: 3 (configurable via `MAX_CONCURRENT_ANALYSES`)
- **Rationale**: Balances speed vs. resource usage (memory, CPU)
- **Impact**: 5 URLs take ~1.5-2x longer than full parallelism but prevents resource exhaustion

### LLM Cost Optimization
- **Individual Calls**: 5 URLs × $0.03 = $0.15 per batch
- **Batch Call**: 1 × $0.03 = $0.03 per batch
- **Savings**: 80% reduction in API costs

### Database Performance
- **Indexes**:
  - `(status, created_at)` on batches for filtering
  - `(batch_id, order_index)` on URLs for ordered retrieval
- **Cascade Deletes**: Automatic cleanup when batch is deleted

## Error Handling

### Partial Failures
- **Threshold**: Batch marked as COMPLETED if ≥2 URLs succeed
- **UI Indication**: Shows "X/Y completed" with warning
- **Failed URLs**: Marked with ❌ icon and error message

### Validation Errors
- **URL Format**: Must be valid HTTP/HTTPS
- **URL Count**: Min 2, max 5
- **Label Mismatch**: Labels array must match URLs length if provided
- **Duplicate URLs**: Not allowed in same batch

### Graceful Degradation
- **WebSocket Failure**: Falls back to polling (2-second interval)
- **Comparison Failure**: Individual results still available
- **LLM Timeout**: Retry with exponential backoff (3 attempts)

## Best Practices

### For Users
1. **Label Your URLs**: Makes results easier to interpret
2. **Name Your Batches**: Helps organize historical analyses
3. **Mix Competitors**: Include your own site for context
4. **Review Opportunities**: Focus on top 3 for maximum impact

### For Developers
1. **Concurrency Limits**: Don't exceed 3 concurrent crawlers
2. **Token Limits**: Keep competitor summaries under 750 tokens each
3. **Error Handling**: Always handle partial batch failures
4. **WebSocket Fallback**: Implement polling as backup

## Future Enhancements

### Phase 2.7: Advanced Features (Planned)
- Historical tracking and trend analysis
- Change detection alerts
- Export to PDF with charts
- Custom comparison templates
- Competitor tagging/grouping

### Phase 2.8: Analytics (Planned)
- Industry benchmarking database
- Market segment averages
- Competitive intelligence reports
- Time-series analysis

### Phase 2.9: Integrations (Planned)
- Slack/email notifications
- API webhooks for automation
- CSV/JSON bulk import
- Google Sheets integration

## Troubleshooting

### Common Issues

**Q: Batch stuck at 99% progress**
A: This is normal. Final comparison generation happens at 99-100%.

**Q: One URL failed, can I still see results?**
A: Yes, if ≥2 URLs succeeded, you'll see partial results with a warning.

**Q: WebSocket disconnected**
A: The UI automatically falls back to polling. You won't lose progress.

**Q: Comparison insights seem generic**
A: Ensure URLs have sufficient content for LLM to analyze. Avoid redirect-only pages.

**Q: Can I analyze the same URL twice?**
A: Not in the same batch. Use separate batches for before/after comparisons.

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/aura/issues
- Documentation: See README.md
- API Reference: See `/docs` endpoint (development only)

---

**Version**: Phase 2 MVP (January 2025)
**Status**: Production Ready
