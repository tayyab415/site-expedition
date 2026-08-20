const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./playwright",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  workers: 1,
  reporter: [["line"]],
  use: {
    baseURL: "http://127.0.0.1:8041",
    viewport: { width: 1440, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    launchOptions: {
      executablePath: process.env.CHROMIUM_PATH || "/snap/bin/chromium",
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    },
  },
  webServer: {
    command: "exec env EXPEDITION_DISABLE_AUTH=1 EXPEDITION_BIND_HOST=127.0.0.1 PYTHONPATH=. python3 -c \"import expedition.ui.serve as server; server.PORT=8041; server.main()\"",
    cwd: "../..",
    url: "http://127.0.0.1:8041/api/session",
    timeout: 30_000,
    reuseExistingServer: false,
  },
});
