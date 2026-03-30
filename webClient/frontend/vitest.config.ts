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
        branches: 90,
        functions: 90,
        lines: 90,
        statements: 90,
        // Per-file overrides for components with long-running network streaming loops
        // that cannot be exercised in unit tests without real network I/O.
        // SpeedTest and DownloadTest use parallel fetch streams (Array.from async
        // arrow functions) and inner while(true) ReadableStream reader loops.
        // v8 counts each async arrow function as a separate "function" entity, so
        // function coverage is structurally low regardless of /* v8 ignore */ pragmas.
        // TraceTest.downloadDetailedResults uses Blob URL + DOM click chain (jsdom
        // limitation) — function coverage is lower than line coverage for this reason.
        'src/components/SpeedTest.tsx': {
          branches: 60,
          functions: 40,
          lines: 45,
          statements: 45,
        },
        'src/components/DownloadTest.tsx': {
          branches: 80,
          functions: 55,
          lines: 90,
          statements: 90,
        },
        'src/components/TraceTest.tsx': {
          branches: 85,
          functions: 60,
          lines: 85,
          statements: 85,
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
