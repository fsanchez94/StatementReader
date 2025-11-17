const { test, expect } = require('@playwright/test');

test.describe('Home Page', () => {
  test('should load the home page successfully', async ({ page }) => {
    // Navigate to the home page
    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check that the page title or heading is visible
    // Adjust this selector based on your actual app structure
    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });

  test('should have working navigation', async ({ page }) => {
    await page.goto('/');

    // Example: Check if navigation links are present
    // Adjust selectors based on your actual navigation structure
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();
  });
});
