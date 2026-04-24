import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('manager UI loads without errors', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))
    await page.goto('/')
    await expect(page).not.toHaveURL(/error/)
    expect(errors).toHaveLength(0)
  })
})
