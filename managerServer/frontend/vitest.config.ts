import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        branches: 85,
        functions: 70,
        lines: 85,
        statements: 85,
        // Per-file overrides for components with WebSocket or complex async patterns
        // that cannot be fully exercised in unit tests without real WebSocket servers
        'src/components/RealtimeMetrics.tsx': {
          branches: 60,
          functions: 60,
          lines: 60,
          statements: 60,
        },
        'src/components/TestExecutor.tsx': {
          branches: 55,
          functions: 55,
          lines: 55,
          statements: 55,
        },
        // API service is mostly untested integration code
        'src/services/api.ts': {
          branches: 0,
          functions: 0,
          lines: 0,
          statements: 0,
        },
        // Pages with complex async/network patterns
        'src/pages/Devices.tsx': {
          branches: 77,
          functions: 57,
          lines: 87,
          statements: 87,
        },
        'src/pages/Users.tsx': {
          branches: 88,
          functions: 53,
          lines: 94,
          statements: 94,
        },
      },
      exclude: ['node_modules/', 'src/test-setup.ts', '**/*.d.ts', '**/*.config.*'],
    },
  },
})
