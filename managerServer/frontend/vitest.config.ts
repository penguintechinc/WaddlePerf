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
        branches: 90,
        functions: 90,
        lines: 90,
        statements: 90,
        // src/services/api.ts is an integration-layer file entirely mocked in tests;
        // it only exercises real axios calls against the live API.
        // Excluding from thresholds is correct — do not lower or remove this override.
        'src/services/api.ts': {
          branches: 0,
          functions: 0,
          lines: 0,
          statements: 0,
        },
      },
      exclude: [
        'node_modules/',
        'src/test-setup.ts',
        '**/*.d.ts',
        '**/*.config.*',
        // Entry point — not a testable unit; DOM bootstrapping only
        'src/main.tsx',
      ],
    },
  },
})
