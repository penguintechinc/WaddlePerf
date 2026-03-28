import { test, expect } from '@playwright/test'

test.describe('Manager UI', () => {
  test('home page loads', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))
    await page.goto('/')
    expect(errors).toHaveLength(0)
  })
})
