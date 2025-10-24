import { test, expect } from '@playwright/test';

test('shows login form on first load', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Giriş')).toBeVisible();
  await expect(page.getByLabel('Kullanıcı Adı')).toBeVisible();
});

