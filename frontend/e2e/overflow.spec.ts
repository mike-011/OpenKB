import { test, expect, type Page } from "@playwright/test";

// Contract spring (#93): no card's text crosses the card's own rectangle at
// any width. Two lessons baked in here:
// 1. The naive leaf check (scrollWidth vs clientWidth) is blind to flex items
//    that grow their own box and spill over the NEIGHBOUR card — the real bug.
// 2. A fresh app has no data, so there are no cards to measure — the API is
//    mocked with fixture KBs carrying LONG unbreakable identifiers (fake
//    values, per the data-hygiene rule) to reproduce production shapes.
const WIDTHS = [1920, 1280, 820];

const FIXTURE_KBS = {
  root: "/data/openkb-kbs",
  knowledge_bases: [
    {
      name: "alpha_kb_00000000000000000001",
      path: "/data/openkb-kbs/alpha_kb_00000000000000000001",
      document_count: 11,
      last_compile: "2026-07-29T23:34:52",
      has_raw: true,
    },
    {
      name: "bravo_kb_00000000000000000002",
      path: "/data/openkb-kbs/bravo_kb_00000000000000000002",
      document_count: 134,
      last_compile: "2026-07-30T06:46:43",
      has_raw: true,
    },
    {
      name: "charlie_kb_00000000000000000003",
      path: "/data/openkb-kbs/charlie_kb_00000000000000000003",
      document_count: 21,
      last_compile: "2026-08-17T21:34:15",
      has_raw: false,
    },
  ],
};

async function mockData(page: Page): Promise<void> {
  await page.route("**/api/v1/kbs*", (route) => route.fulfill({ json: FIXTURE_KBS }));
  await page.route("**/api/v1/chat/sessions*", (route) =>
    route.fulfill({
      json: {
        kb: "alpha_kb_00000000000000000001",
        sessions: [
          {
            id: "s1",
            title: "A session with a long title that wraps gracefully",
            turn_count: 4,
            updated_at: "2026-11-17T21:45:00",
            model: "mimo-v2.6-flash",
          },
        ],
      },
    }),
  );
}

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
  await mockData(page);
  for (const url of ["/", "/kb", "/settings"]) {
    for (const w of WIDTHS) {
      await page.setViewportSize({ width: w, height: 900 });
      await mockData(page);
      await page.goto(url);
      await page.waitForLoadState("networkidle");
      const bad = await cardSpills(page);
      expect(bad, `${url} @ ${w}px spills: ${JSON.stringify(bad)}`).toEqual([]);
    }
  }
});
