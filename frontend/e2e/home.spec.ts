/**
 * E2E tests for home page
 */

import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should display the landing page', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page).toHaveTitle(/Aura/);

    // Check hero section
    await expect(page.getByRole('heading', { name: /Optimize for Search/i })).toBeVisible();
    await expect(page.getByText(/AI Engines/i)).toBeVisible();

    // Check description
    await expect(page.getByText(/Analyze your website's SEO performance/i)).toBeVisible();
  });

  test('should display URL input form', async ({ page }) => {
    await page.goto('/');

    // Check form elements
    await expect(page.getByLabel(/Website URL/i)).toBeVisible();
    await expect(page.getByPlaceholder(/https:\/\/example.com/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Analyze Website/i })).toBeVisible();
  });

  test('should display feature cards', async ({ page }) => {
    await page.goto('/');

    // Check all three feature cards
    await expect(page.getByText(/SEO Analysis/i)).toBeVisible();
    await expect(page.getByText(/AEO Insights/i)).toBeVisible();
    await expect(page.getByText(/Actionable Recommendations/i)).toBeVisible();
  });

  test('should validate empty URL', async ({ page }) => {
    await page.goto('/');

    // Click submit without entering URL
    await page.getByRole('button', { name: /Analyze Website/i }).click();

    // Check error message
    await expect(page.getByText(/Please enter a URL/i)).toBeVisible();
  });

  test('should validate invalid URL', async ({ page }) => {
    await page.goto('/');

    // Enter invalid URL
    await page.getByLabel(/Website URL/i).fill('not-a-valid-url');
    await page.getByRole('button', { name: /Analyze Website/i }).click();

    // Check error message
    await expect(page.getByText(/Please enter a valid HTTP or HTTPS URL/i)).toBeVisible();
  });

  test('should validate non-HTTP URL', async ({ page }) => {
    await page.goto('/');

    // Enter non-HTTP URL
    await page.getByLabel(/Website URL/i).fill('ftp://example.com');
    await page.getByRole('button', { name: /Analyze Website/i }).click();

    // Check error message
    await expect(page.getByText(/Please enter a valid HTTP or HTTPS URL/i)).toBeVisible();
  });

  test('should show loading state on submit', async ({ page }) => {
    await page.goto('/');

    // Mock the API to delay response
    await page.route('**/api/v1/analysis', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 201,
        body: JSON.stringify({
          id: 'test-123',
          url: 'https://example.com',
          status: 'pending',
          progress: 0,
          created_at: new Date().toISOString(),
        }),
      });
    });

    // Enter valid URL
    await page.getByLabel(/Website URL/i).fill('https://example.com');

    // Click submit
    await page.getByRole('button', { name: /Analyze Website/i }).click();

    // Check loading state
    await expect(page.getByText(/Analyzing.../i)).toBeVisible();
  });
});
