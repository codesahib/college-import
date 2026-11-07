import { defineConfig, devices } from '@playwright/test'
import path from 'node:path'
const root = path.resolve(import.meta.dirname, '..')
const python = process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python'
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['json', { outputFile: '../evidence/playwright-results.json' }]],
  use: {
    ...devices['Desktop Chrome'],
    baseURL: 'http://127.0.0.1:5174',
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `${python} scripts/reset.py --empty --database backend/e2e.sqlite3 && ${python} -m uvicorn backend.main:app --host 127.0.0.1 --port 8002`,
      cwd: root,
      env: { IMPORT_DB: path.join(root, 'backend/e2e.sqlite3') },
      url: 'http://127.0.0.1:8002/api/health',
      reuseExistingServer: false,
    },
    { command: 'npm run dev', url: 'http://127.0.0.1:5174', reuseExistingServer: false },
  ],
})
