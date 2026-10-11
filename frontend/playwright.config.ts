import { defineConfig, devices } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

const frontendUrl =
  process.env.SUBABOT_TEST_FRONTEND_URL || "http://127.0.0.1:4330";
const backendUrl =
  process.env.SUBABOT_TEST_BACKEND_URL || "http://127.0.0.1:8030";
const frontendPort = new URL(frontendUrl).port;
const backendPort = new URL(backendUrl).port;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: frontendUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      command: `uv run --frozen --directory ../backend uvicorn subabot.api:app --host 127.0.0.1 --port ${backendPort}`,
      url: `${backendUrl}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
      env: {
        SUBABOT_DATABASE_URL: `sqlite:///${join(tmpdir(), `subabot-e2e-${process.pid}.db`)}`,
        SUBABOT_SCHEDULER_ENABLED: "false",
        SUBABOT_SCAN_COOLDOWN_SECONDS: "0",
        SUBABOT_FRONTEND_URL: frontendUrl,
      },
    },
    {
      command: `npm start`,
      url: frontendUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
      env: {
        BACKEND_URL: backendUrl,
        PUBLIC_SITE_URL: frontendUrl,
        HOST: "127.0.0.1",
        PORT: frontendPort,
      },
    },
  ],
});
