import { defineConfig } from "@playwright/test";

// UI e2e skeleton: boots the packaged REST app (openkb wheel install,
// factory entry point) and runs DOM-level smoke against the Studio shell.
// No LLM calls, no fixture KB required.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: { baseURL: "http://127.0.0.1:8123" },
  webServer: {
    command: "python3 -m uvicorn openkb.api:create_app --factory --port 8123",
    url: "http://127.0.0.1:8123/",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
