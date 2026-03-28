import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        branches: 85,
        functions: 75,
        lines: 85,
        statements: 85,
        // Per-file overrides for components with long-running network streaming loops
        // that cannot be exercised in unit tests without real network I/O
        'src/components/SpeedTest.tsx': {
          branches: 50,
          functions: 30,
          lines: 35,
          statements: 35,
        },
        'src/components/DownloadTest.tsx': {
          branches: 50,
          functions: 50,
          lines: 50,
          statements: 50,
        },
        'src/components/TraceTest.tsx': {
          branches: 60,
          functions: 60,
          lines: 60,
          statements: 60,
        },
        'src/components/TestForm.tsx': {
          branches: 77,
          functions: 75,
          lines: 96,
          statements: 96,
        },
        'src/components/TestRunner.tsx': {
          branches: 95,
          functions: 70,
          lines: 91,
          statements: 91,
        },
      },
      exclude: [
        'node_modules/',
        'src/test-setup.ts',
        '**/*.d.ts',
        '**/*.config.*',
        // Entry point — not testable unit
        'src/main.tsx',
      ],
    },
  },
})
