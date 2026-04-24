import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('login validates empty fields', async ({ page }) => {
    await page.goto('/login')
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")')
    // Should show validation error, not navigate away
    await expect(page).toHaveURL(/login/)
  })

  test('login rejects invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"], input[name="email"]', 'wrong@test.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")')
    await expect(page.locator('text=/invalid|error|incorrect/i')).toBeVisible({ timeout: 5000 })
  })
})
