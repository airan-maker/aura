/**
 * E2E tests for analysis flow
 */

import { test, expect } from '@playwright/test';

test.describe('Analysis Flow', () => {
  test('should submit URL and navigate to analysis page', async ({ page }) => {
    await page.goto('/');

    // Mock API response for creating analysis
    await page.route('**/api/v1/analysis', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          body: JSON.stringify({
            id: 'test-analysis-123',
            url: 'https://example.com',
            status: 'pending',
            progress: 0,
            created_at: new Date().toISOString(),
          }),
        });
      }
    });

    // Enter URL and submit
    await page.getByLabel(/Website URL/i).fill('https://example.com');
    await page.getByRole('button', { name: /Analyze Website/i }).click();

    // Should navigate to analysis page
    await expect(page).toHaveURL(/\/analysis\/test-analysis-123/);
  });

  test('should display analysis progress page', async ({ page }) => {
    const requestId = 'test-analysis-456';

    // Mock status API
    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'processing',
          progress: 45,
          current_step: 'Analyzing SEO metrics',
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto(`/analysis/${requestId}`);

    // Check page elements
    await expect(page.getByText(/Analyzing Your Website/i)).toBeVisible();
    await expect(page.getByText(/https:\/\/example.com/i)).toBeVisible();
    await expect(page.getByText(/45%/i)).toBeVisible();
    await expect(page.getByText(/Analyzing SEO metrics/i)).toBeVisible();
  });

  test('should show pending status', async ({ page }) => {
    const requestId = 'test-pending-789';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://example.com',
          status: 'pending',
          progress: 0,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto(`/analysis/${requestId}`);

    // Check pending status
    await expect(page.getByText(/Waiting to start/i)).toBeVisible();
  });

  test('should show error status', async ({ page }) => {
    const requestId = 'test-error-999';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: requestId,
          url: 'https://invalid-domain.com',
          status: 'failed',
          progress: 30,
          error_message: 'Failed to connect to website',
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto(`/analysis/${requestId}`);

    // Check error display
    await expect(page.getByText(/Analysis failed/i)).toBeVisible();
    await expect(page.getByText(/Failed to connect to website/i)).toBeVisible();
  });

  test('should redirect to report when completed', async ({ page }) => {
    const requestId = 'test-completed-111';

    // Mock status as completed
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

    await page.goto(`/analysis/${requestId}`);

    // Should redirect to report page after delay
    await page.waitForURL(`/report/${requestId}`, { timeout: 3000 });
    await expect(page).toHaveURL(`/report/${requestId}`);
  });

  test('should handle 404 for non-existent analysis', async ({ page }) => {
    const requestId = 'non-existent-request';

    await page.route(`**/api/v1/analysis/${requestId}`, async (route) => {
      await route.fulfill({
        status: 404,
        body: JSON.stringify({
          detail: 'Analysis request not found',
        }),
      });
    });

    await page.goto(`/analysis/${requestId}`);

    // Should show error
    await expect(page.getByText(/Error Loading Analysis/i)).toBeVisible();
  });
});
