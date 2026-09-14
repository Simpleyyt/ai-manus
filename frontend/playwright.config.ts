import { defineConfig } from '@playwright/test'

// Browser e2e against the running dev stack (./dev.sh up -d):
// frontend :5173, backend :8000, mockserver :8090 (scenario control).
// The mockserver replay index is global state — run tests serially.
export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure'
  },
  outputDir: './test-results'
})
