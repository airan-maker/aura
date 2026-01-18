# Aura Frontend

Next.js 14+ frontend for the Aura SEO & AEO analysis platform.

## Features

- **Modern Stack**: Next.js 14 with App Router, React Server Components
- **TypeScript**: Full type safety throughout the application
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Real-time Updates**: WebSocket integration for live analysis progress
- **Responsive Design**: Mobile-first approach with responsive layouts
- **API Integration**: Clean separation with dedicated API client layer

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Home page (URL input)
│   │   ├── analysis/[id]/     # Analysis progress page
│   │   ├── report/[id]/       # Report dashboard
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   └── ProgressBar.tsx
│   │   ├── analysis/         # Analysis-specific components
│   │   │   ├── UrlInputForm.tsx
│   │   │   └── ProgressTracker.tsx
│   │   └── report/           # Report visualization components
│   │       ├── ScoreGauge.tsx
│   │       ├── SEOMetricsCard.tsx
│   │       ├── AEOInsightsCard.tsx
│   │       └── RecommendationList.tsx
│   ├── lib/                  # Utility libraries
│   │   └── api-client.ts    # Backend API client
│   ├── hooks/               # Custom React hooks
│   │   ├── useAnalysis.ts   # Analysis state management
│   │   └── useWebSocket.ts  # WebSocket connection
│   └── types/               # TypeScript type definitions
│       └── index.ts
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Docker Development

Run with Docker Compose (from project root):
```bash
docker-compose up frontend
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build production bundle
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Key Components

### Pages

#### Home (`/`)
- URL input form for starting new analysis
- Hero section with feature highlights
- Validates URLs before submission

#### Analysis Progress (`/analysis/[id]`)
- Real-time progress tracking with WebSocket
- Fallback to polling if WebSocket unavailable
- Auto-redirects to report when completed
- Error handling with user-friendly messages

#### Report Dashboard (`/report/[id]`)
- SEO & AEO score gauges with visual indicators
- Detailed metrics breakdown
- AI-powered insights
- Filterable recommendations list

### Components

#### UI Components
- **Button**: Reusable button with variants (primary, secondary, danger)
- **Card**: Container component for content sections
- **ProgressBar**: Animated progress indicator

#### Analysis Components
- **UrlInputForm**: URL validation and submission
- **ProgressTracker**: Status display with icons and progress bar

#### Report Components
- **ScoreGauge**: Canvas-based circular score visualization
- **SEOMetricsCard**: Detailed SEO analysis display
- **AEOInsightsCard**: AI-generated insights display
- **RecommendationList**: Filterable, priority-based recommendations

### Custom Hooks

#### `useAnalysis(requestId, options)`
Manages analysis state with automatic polling:
- Fetches analysis status
- Polls for updates until completion
- Auto-fetches results when completed
- Returns: `{ analysis, result, loading, error, refetch }`

#### `useWebSocket(requestId)`
Handles WebSocket connection for real-time updates:
- Auto-connects to backend WebSocket
- Receives progress updates
- Auto-reconnects on disconnect
- Implements ping/pong keep-alive
- Returns: `{ connected, progress, step, status, error, disconnect, reconnect }`

### API Client

The `api-client.ts` module provides:
- `createAnalysis(url)` - Submit new analysis
- `getAnalysisStatus(requestId)` - Get current status
- `getAnalysisResults(requestId)` - Get completed results
- `listAnalyses(skip, limit)` - List all analyses
- `createWebSocket(requestId)` - Create WebSocket connection
- `healthCheck()` - Backend health check

All functions include:
- Automatic error handling
- Type-safe responses
- Network error recovery

## Styling

The project uses Tailwind CSS with custom color schemes:

- **Primary**: Blue tones for main actions and links
- **Success**: Green for positive states (high scores)
- **Warning**: Yellow for moderate states (medium scores)
- **Danger**: Red for negative states (low scores, errors)

Custom configuration in `tailwind.config.ts` provides 50-900 shades for each color.

## Type Safety

All API responses and component props are fully typed using TypeScript interfaces defined in `src/types/index.ts`:

- `AnalysisRequest` - Analysis request model
- `AnalysisResult` - Complete analysis results
- `SEOMetrics` - SEO analysis data
- `AEOMetrics` - AEO analysis data
- `Recommendation` - Recommendation item
- `WebSocketMessage` - WebSocket message format

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Tips

### Hot Reload
Next.js supports fast refresh - changes to components will reflect immediately without losing state.

### API URL Configuration
- Development: `http://localhost:8000/api/v1`
- Production: Set `NEXT_PUBLIC_API_URL` environment variable

### WebSocket Connection
The WebSocket URL is automatically derived from the API URL by replacing `http` with `ws`.

## Troubleshooting

### "Cannot connect to backend"
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` environment variable
- Verify CORS settings in backend

### "WebSocket connection failed"
- Check if backend WebSocket endpoint is accessible
- Verify firewall/proxy settings
- WebSocket will gracefully fall back to polling

### Styles not applying
- Clear `.next` cache: `rm -rf .next`
- Rebuild: `npm run build`
- Check Tailwind configuration

## Performance Optimization

- Server-side rendering for initial page load
- Client-side navigation for subsequent pages
- Automatic code splitting by route
- Image optimization with Next.js Image component (if images added)
- Canvas-based gauge rendering for performance

## Future Enhancements

Potential additions for future versions:
- PDF report export
- Historical analysis comparison
- Scheduled re-analysis
- Multi-page analysis
- Competitor comparison
- Custom branding options

## Contributing

1. Follow TypeScript strict mode
2. Use functional components with hooks
3. Maintain component modularity
4. Add prop types for all components
5. Test on multiple browsers
6. Follow Tailwind utility-first approach

## License

Part of the Aura project. See main README for details.
