import { expect, test } from "@playwright/test";

test("app shell loads with zero page errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(String(err)));
  await page.goto("/");
  await expect(page).toHaveTitle(/OpenKB Studio/);
  await expect(page.locator("body")).not.toBeEmpty();
  expect(errors).toEqual([]);
});

test("deep links fall back to the SPA", async ({ page }) => {
  const resp = await page.goto("/some/deep/route");
  expect(resp?.status()).toBeLessThan(500);
  await expect(page).toHaveTitle(/OpenKB Studio/);
});

test("REST API answers from the app origin", async ({ request }) => {
  const resp = await request.get("/api/v1/config");
  expect(resp.status()).toBeLessThan(500);
});

test("about shows build line, fork credit and thanks list", async ({ page }) => {
  await page.goto("/#/settings");
  await page.getByText("About", { exact: true }).click();
  await expect(page.getByText(/^build:/)).toBeVisible();
  await expect(page.getByText(/fork: OpenKB Community Edition by sysadmins/)).toBeVisible();
  await expect(page.getByText("Forked repo — mike-011/OpenKB")).toBeVisible();
  await expect(page.getByText("Thanks to:")).toBeVisible();
});
