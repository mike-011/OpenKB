import { test, expect } from "@playwright/test";

// Design-contract spring (#94): "looks clickable -> IS clickable".
// The connector cards on /settings (no knowledge base selected) render as
// styled blocks with a call to action ("Open a knowledge base to connect X")
// but carry no link/button at all — the owner could not tell whether they
// were controls or an advert. Each card must act (navigate to the KB list).
test("connector cards on settings act as links or buttons", async ({ page }) => {
  await page.goto("/#/settings");
  await page.getByText("Data sources", { exact: true }).click();
  for (const label of ["Google Drive", "Amazon S3", "OneDrive"]) {
    const card = page.locator("a, button").filter({ hasText: label });
    await expect(
      card,
      `connector card "${label}" must be a link or button (design contract)`,
    ).toHaveCount(1);
  }
});
