import { test, expect, type Page } from "@playwright/test";

// Contract spring (#93): no card's text crosses the card's own rectangle at
// any width. The naive leaf check (scrollWidth vs clientWidth) is blind to
// flex items that grow their own box and spill over the neighbouring card —
// exactly the reported bug — so the contract is measured as geometry: every
// leaf text node must fit inside its enclosing card/button rect.
const WIDTHS = [1920, 1280, 820];

async function cardSpills(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const bad: string[] = [];
    const cards = document.querySelectorAll<HTMLElement>(
      "button, article, [class*='rounded-2xl'], [class*='rounded-apple-md']",
    );
    for (const card of cards) {
      const cr = card.getBoundingClientRect();
      if (cr.width < 40 || cr.height < 20) continue;
      card.querySelectorAll<HTMLElement>("*").forEach((e) => {
        if (e.children.length !== 0) return;
        const text = e.textContent?.trim();
        if (!text) return;
        const r = e.getBoundingClientRect();
        if (r.width === 0) return;
        if (r.right > cr.right + 2 || r.left < cr.left - 2) {
          bad.push(
            `"${text.slice(0, 30)}" crosses its card at x=${Math.round(r.right)}>${Math.round(cr.right)}`,
          );
        }
      });
    }
    return bad;
  });
}

test("no card text crosses its card at any width", async ({ page }) => {
  for (const url of ["/", "/kb", "/settings"]) {
    for (const w of WIDTHS) {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto(url);
      await page.waitForLoadState("networkidle");
      const bad = await cardSpills(page);
      expect(bad, `${url} @ ${w}px spills: ${JSON.stringify(bad)}`).toEqual([]);
    }
  }
});
