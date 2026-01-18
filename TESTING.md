# Aura Testing Documentation

## Overview

This document provides comprehensive testing instructions for the Aura platform.

## Test Types

### 1. Unit Tests (Backend)

**Location**: `backend/tests/`

**Run all unit tests:**
```bash
cd backend
pytest -v
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
# View report: open htmlcov/index.html
```

**Run specific test modules:**
```bash
# Crawler tests
pytest tests/test_services/test_crawler.py -v

# SEO analyzer tests
pytest tests/test_services/test_seo_analyzer.py -v

# LLM analyzer tests
pytest tests/test_services/test_llm_analyzer.py -v

# Integration tests
pytest tests/test_integration/test_full_pipeline.py -v
```

**Expected results:**
- All tests should pass
- Coverage should be > 80%

### 2. E2E Tests (Frontend)

**Location**: `frontend/e2e/`

**Setup:**
```bash
cd frontend
npm install
npx playwright install
```

**Run E2E tests:**
```bash
# Headless mode (default)
npm test

# With UI
npm run test:ui

# Headed mode (see browser)
npm run test:headed

# Specific test file
npx playwright test e2e/home.spec.ts
```

**Test files:**
- `home.spec.ts` - Home page tests (URL input, validation)
- `analysis.spec.ts` - Analysis flow tests (progress tracking, WebSocket)
- `report.spec.ts` - Report page tests (score display, recommendations)

**Expected results:**
- All E2E tests should pass
- Tests should work on Chrome, Firefox, Safari, and Mobile Chrome

### 3. Integration Tests

**Full pipeline tests:**
```bash
cd backend
pytest tests/test_integration/test_full_pipeline.py -v
```

**Tests included:**
- Complete analysis pipeline (crawl → SEO → LLM → save)
- Progress tracking
- Error handling
- Concurrent analyses
- Duration tracking
- Screenshot capture

### 4. System Tests

**Automated system test:**
```bash
./scripts/test-system.sh
```

This script tests:
1. Docker services status
2. Backend health endpoint
3. Frontend accessibility
4. Database connection
5. Backend unit tests
6. API endpoints (create, status, results)
7. Full analysis completion
8. Frontend E2E tests (if Playwright installed)

**Expected output:**
```
================================
Test Summary
================================
Passed: 9
Failed: 0

All tests passed! ✓
```

### 5. Website Testing

**Test with multiple real websites:**
```bash
./scripts/test-websites.sh
```

Tests these websites:
- https://example.com
- https://www.ietf.org
- https://www.w3.org
- https://developer.mozilla.org
- https://github.com

**Expected results:**
- 100% success rate (all 5 websites)
- Average duration: 60-90 seconds per analysis
- SEO scores: 50-95 range
- AEO scores: 60-90 range

### 6. Quick Test

**Fast health check:**
```bash
./scripts/quick-test.sh
```

Performs:
- Backend health check
- Frontend accessibility check
- Creates one test analysis

**Use case:** Verify system is running correctly after startup

## Manual Testing Checklist

### Frontend UI Flow

**Home Page:**
- [ ] Page loads without errors
- [ ] Hero section displays correctly
- [ ] URL input form is visible
- [ ] Feature cards display (3 cards)
- [ ] Empty URL shows error
- [ ] Invalid URL shows error ("not-a-url")
- [ ] Non-HTTP URL shows error ("ftp://example.com")
- [ ] Valid URL accepts ("https://example.com")
- [ ] Submit button shows loading state
- [ ] Successful submit navigates to /analysis/[id]

**Analysis Progress Page:**
- [ ] URL displays correctly
- [ ] Progress bar animates
- [ ] Percentage updates (0% → 100%)
- [ ] Current step text updates
- [ ] Status icons change (pending → processing → completed)
- [ ] WebSocket connection indicator shows
- [ ] Completed status auto-redirects to report (after ~1.5s)
- [ ] Failed status shows error message
- [ ] Error has "Go Back Home" button

**Report Page:**
- [ ] Header shows "Analysis Report"
- [ ] URL link is clickable
- [ ] Duration and timestamp display
- [ ] SEO score gauge renders correctly
- [ ] AEO score gauge renders correctly
- [ ] Score colors correct (green: 80+, yellow: 60-79, red: <60)
- [ ] SEO Metrics card shows all 6 categories
- [ ] Each category shows score and issues
- [ ] AEO Insights card shows clarity score
- [ ] AEO shows AI-generated insights
- [ ] Recommendations list displays
- [ ] Recommendation count badges correct
- [ ] Filter buttons work (All, High, Medium, Low)
- [ ] High priority items have red badges
- [ ] Medium priority items have yellow badges
- [ ] Low priority items have blue badges
- [ ] "New Analysis" button navigates to home

### Backend API

**Health Check:**
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok"}
```

**Create Analysis:**
```bash
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
# Expected: {"id":"...", "status":"pending", "progress":0, ...}
```

**Get Status:**
```bash
curl http://localhost:8000/api/v1/analysis/{REQUEST_ID}
# Expected: {"id":"...", "status":"processing", "progress":45, ...}
```

**Get Results:**
```bash
curl http://localhost:8000/api/v1/analysis/{REQUEST_ID}/results
# Expected: {"seo_score":87.5, "aeo_score":82.3, ...}
```

**List Analyses:**
```bash
curl http://localhost:8000/api/v1/analysis
# Expected: [{"id":"...", ...}, ...]
```

### WebSocket

**Browser Console Test:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/{REQUEST_ID}/ws');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Disconnected');

// Send ping every 30s
setInterval(() => ws.send('ping'), 30000);
```

Expected messages:
- `{"type": "progress", "progress": 30, "step": "Crawling website"}`
- `{"type": "progress", "progress": 60, "step": "SEO analysis completed"}`
- `{"type": "completed", "progress": 100, "status": "completed"}`

## Performance Testing

### Load Time Benchmarks

**Target metrics:**
- Homepage load: < 3s
- Analysis creation: < 500ms (API call)
- Analysis completion: 60-90s
- Report page load: < 2s

**Measure:**
```bash
# Homepage
time curl -s http://localhost:3000 > /dev/null

# API response time
time curl -s -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' > /dev/null

# Full analysis (from create to results)
./scripts/test-websites.sh
```

### Resource Usage

**Monitor with Docker:**
```bash
docker stats

# Expected usage:
# Backend: CPU 10-30%, Memory 200-400MB
# Frontend: CPU 5-10%, Memory 100-200MB
# PostgreSQL: CPU 5-10%, Memory 50-100MB
```

## Error Scenarios

### Test Error Handling

1. **Invalid URL Formats:**
   - Not a URL: `not-a-url`
   - Missing protocol: `example.com`
   - Non-HTTP: `ftp://example.com`
   - Expected: Validation error, no API call

2. **Non-existent Domain:**
   - URL: `https://this-definitely-does-not-exist-12345.com`
   - Expected: Analysis fails at crawling stage, error message shown

3. **SSRF Protection:**
   - URL: `http://localhost:8000`
   - URL: `http://127.0.0.1`
   - URL: `http://192.168.1.1`
   - Expected: Validation error "potentially unsafe URL"

4. **Timeout:**
   - Very slow website (need to mock)
   - Expected: Timeout after 30s, error message

5. **OpenAI API Failure:**
   - Remove/invalidate API key
   - Expected: Analysis fails at LLM stage, retries 3 times, then fails

6. **Database Connection Loss:**
   - Stop PostgreSQL: `docker-compose stop db`
   - Expected: Backend returns 500 errors

7. **Backend Restart During Analysis:**
   - Start analysis, restart backend mid-process
   - Expected: Analysis marked as failed or remains in processing

## Test Data

### Good SEO Examples (Expected High Scores)
- https://developer.mozilla.org (85-95)
- https://www.w3.org (80-90)
- https://github.com (80-90)

### Poor SEO Examples (Expected Lower Scores)
- http://info.cern.ch (30-50) - First website, minimal SEO
- Sites without HTTPS (penalty)
- Sites without meta description (penalty)

### Edge Cases
- Very large pages (>10MB HTML)
- Pages with many redirects
- Pages requiring authentication (will fail)
- Pages blocking bots (may fail)

## Continuous Integration

### GitHub Actions (Future)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d db
          cd backend
          pytest --cov=app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run E2E tests
        run: |
          cd frontend
          npm install
          npx playwright install
          npm test
```

## Troubleshooting Tests

### Backend Tests Fail

**"No module named 'app'"**
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

**"playwright executable doesn't exist"**
```bash
playwright install chromium
```

**"Database connection refused"**
```bash
docker-compose up -d db
docker-compose exec backend alembic upgrade head
```

### Frontend Tests Fail

**"Cannot connect to http://localhost:3000"**
```bash
# Ensure frontend is running
docker-compose up -d frontend
# Or manually: cd frontend && npm run dev
```

**"WebSocket connection failed"**
- Check backend is running
- Verify WebSocket endpoint in code
- Check browser console for errors

### Integration Tests Timeout

- Increase timeout values in test config
- Check OpenAI API key is valid
- Verify network connectivity
- Check if rate limited by OpenAI

## Success Criteria

Phase 1.7 is complete when:
- [ ] All backend unit tests pass (100%)
- [ ] All frontend E2E tests pass (100%)
- [ ] Integration tests pass (100%)
- [ ] System test script passes
- [ ] 10+ real websites tested successfully
- [ ] Average analysis time < 90s
- [ ] Success rate > 90%
- [ ] No critical bugs remaining
- [ ] Documentation complete

## Next Steps

After testing phase:
- Fix any discovered bugs
- Optimize performance bottlenecks
- Improve error messages
- Add more test coverage
- Prepare for Phase 1.8 (Deployment)
