import { defineConfig, devices } from '@playwright/test'
import { execFileSync } from 'child_process'
import path from 'path'

const repoName = path.basename(
  execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' }).trim()
)

export default defineConfig({
  testDir: '.',
  outputDir: `/tmp/playwright-${repoName}`,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['html'], ['list']],
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'manager',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:3000',
      },
      testMatch: ['**/manager.spec.ts', '**/smoke.spec.ts'],
    },
    {
      name: 'webclient',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:3001',
      },
      testMatch: ['**/webclient.spec.ts', '**/auth.spec.ts'],
    },
  ],
})
