import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration.
 *
 * In this environment Playwright browsers are pre-installed under
 * `/opt/pw-browsers`; we point `executablePath` at the vendored Chromium and
 * skip the automatic browser download (set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
 * in the shell). Locally, run `npx playwright install chromium` once instead
 * and remove `executablePath`.
 */
const VENDORED_CHROMIUM = process.env.PLAYWRIGHT_CHROMIUM_PATH ?? '/opt/pw-browsers/chromium';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    // Mobile-first: emulate a phone viewport for all specs.
    ...devices['Pixel 7'],
    launchOptions: {
      executablePath: VENDORED_CHROMIUM,
    },
  },
  projects: [
    {
      name: 'mobile-chromium',
      use: { ...devices['Pixel 7'], launchOptions: { executablePath: VENDORED_CHROMIUM } },
    },
  ],
  // Start the dev server automatically unless one is already running.
  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
