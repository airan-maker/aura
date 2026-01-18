/**
 * E2E tests for report page
 */

import { test, expect } from '@playwright/test';

// Mock analysis result data
const mockResult = {
  id: 'result-123',
  request_id: 'test-request-123',
  url: 'https://example.com',
  seo_score: 87.5,
  seo_metrics: {
    meta_tags: {
      title_present: true,
      title_length: 45,
      description_present: true,
      description_length: 120,
      og_tags_present: true,
      score: 100,
      issues: [],
    },
    headings: {
      h1_count: 1,
      h1_text: 'Example Domain',
      heading_hierarchy_valid: true,
      score: 100,
      issues: [],
    },
    performance: {
      load_time: 1.2,
      score: 95,
      issues: [],
    },
    mobile: {
      viewport_tag_present: true,
      score: 100,
      issues: [],
    },
    security: {
      https: true,
      score: 100,
      issues: [],
    },
    structured_data: {
      present: false,
      types: [],
      score: 0,
      issues: ['No structured data found'],
    },
  },
  aeo_score: 82.3,
  aeo_metrics: {
    what_it_does: 'Example domain for illustrative examples in documents',
    products_services: 'Domain registration examples',
    target_audience: 'Developers and technical writers',
    unique_value: 'Reserved example domain',
    clarity_score: 8,
    overall_impression: 'Clear and simple domain for documentation purposes',
  },
  recommendations: [
    {
      category: 'seo',
      priority: 'high',
      title: 'Add Structured Data',
      description: 'Implement JSON-LD structured data to help search engines understand your content better.',
      impact: 'Improved search result appearance and better AI understanding',
    },
    {
      category: 'seo',
      priority: 'medium',
      title: 'Optimize Page Speed',
      description: 'Consider adding CDN and optimizing images to improve load time.',
      impact: 'Better user experience and search rankings',
    },
    {
      category: 'aeo',
      priority: 'low',
      title: 'Enhance Value Proposition',
      description: 'Make your unique value proposition more prominent in the content.',
      impact: 'Better AI-powered recommendations',
    },
  ],
  analysis_duration: 45.2,
  created_at: new Date().toISOString(),
};

test.describe('Report Page', () => {
  test('should display report dashboard', async ({ page }) => {
    const requestId = 'test-request-123';

    // Mock analysis request
    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
        }),
      });
    });

    // Mock analysis results
    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Check page header
    await expect(page.getByRole('heading', { name: /Analysis Report/i })).toBeVisible();
    await expect(page.getByText(/https:\/\/example.com/i)).toBeVisible();
  });

  test('should display score gauges', async ({ page }) => {
    const requestId = 'test-request-456';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Check score labels
    await expect(page.getByText('SEO Score')).toBeVisible();
    await expect(page.getByText('AEO Score')).toBeVisible();

    // Check score quality labels
    await expect(page.getByText('Excellent')).toBeVisible(); // For scores above 80
  });

  test('should display SEO metrics card', async ({ page }) => {
    const requestId = 'test-request-789';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Check SEO metrics sections
    await expect(page.getByText('SEO Analysis')).toBeVisible();
    await expect(page.getByText('Meta Tags')).toBeVisible();
    await expect(page.getByText('Heading Structure')).toBeVisible();
    await expect(page.getByText('Performance')).toBeVisible();
    await expect(page.getByText('Mobile Optimization')).toBeVisible();
    await expect(page.getByText('Security')).toBeVisible();
    await expect(page.getByText('Structured Data')).toBeVisible();
  });

  test('should display AEO insights card', async ({ page }) => {
    const requestId = 'test-request-999';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Check AEO sections
    await expect(page.getByText('AI Engine Optimization (AEO) Analysis')).toBeVisible();
    await expect(page.getByText('Clarity Score')).toBeVisible();
    await expect(page.getByText('What This Website Does')).toBeVisible();
    await expect(page.getByText(/Example domain for illustrative examples/i)).toBeVisible();
  });

  test('should display recommendations list', async ({ page }) => {
    const requestId = 'test-request-111';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Check recommendations section
    await expect(page.getByText('Recommendations')).toBeVisible();
    await expect(page.getByText('Add Structured Data')).toBeVisible();
    await expect(page.getByText('Optimize Page Speed')).toBeVisible();
    await expect(page.getByText('Enhance Value Proposition')).toBeVisible();
  });

  test('should filter recommendations by priority', async ({ page }) => {
    const requestId = 'test-request-222';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Click high priority filter
    await page.getByRole('button', { name: /High Priority/i }).click();

    // Should show only high priority recommendations
    await expect(page.getByText('Add Structured Data')).toBeVisible();

    // Should hide medium and low priority
    await expect(page.getByText('Optimize Page Speed')).not.toBeVisible();
    await expect(page.getByText('Enhance Value Proposition')).not.toBeVisible();
  });

  test('should have New Analysis button', async ({ page }) => {
    const requestId = 'test-request-333';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'completed',
          progress: 100,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Check New Analysis button
    const newAnalysisButton = page.getByRole('button', { name: /New Analysis/i });
    await expect(newAnalysisButton).toBeVisible();

    // Click should navigate to home
    await newAnalysisButton.click();
    await expect(page).toHaveURL('/');
  });

  test('should handle incomplete analysis', async ({ page }) => {
    const requestId = 'test-request-444';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'processing',
          progress: 50,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/analysis/${requestId}/results`, async (route) => {
      await route.fulfill({
        status: 400,
        body: JSON.stringify({
          detail: 'Analysis is not completed yet. Current status: processing',
        }),
      });
    });

    await page.goto(`/report/${requestId}`);

    // Should show error
    await expect(page.getByText(/Error Loading Report/i)).toBeVisible();
  });
});
