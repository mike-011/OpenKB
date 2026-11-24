import { test, expect, type Page } from "@playwright/test";

// Contract spring (#93): no leaf text node spills out of its box at any width.
// A node that overflows but is properly clipped (overflow hidden / ellipsis)
// is fine — a visible spill is not. Widths chosen per the owner's report that
// the drift differs per display.
const WIDTHS = [1920, 1280, 820];

async function spillingLeaves(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const bad: string[] = [];
    document.querySelectorAll<HTMLElement>("*").forEach((e) => {
      if (e.children.length !== 0) return;
      const text = e.textContent?.trim();
      if (!text || e.clientWidth === 0) return;
      if (e.scrollWidth <= e.clientWidth + 2) return;
      const cs = getComputedStyle(e);
      const clipped = cs.overflowX === "hidden" || cs.textOverflow === "ellipsis";
      if (!clipped) bad.push(text.slice(0, 40));
    });
    return bad;
  });
}

test("no text spills out of its box at any width", async ({ page }) => {
  for (const url of ["/", "/kb", "/settings"]) {
    for (const w of WIDTHS) {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto(url);
      await page.waitForLoadState("networkidle");
      const bad = await spillingLeaves(page);
      expect(bad, `${url} @ ${w}px spills: ${JSON.stringify(bad)}`).toEqual([]);
    }
  }
});
