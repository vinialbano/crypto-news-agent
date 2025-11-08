import { test, expect } from "@playwright/test";

test.describe("Articles page", () => {
  test("navigates from navbar and shows ingestion controls", async ({
    page,
  }) => {
    await page.goto("/");

    // Navigate via navbar
    await page.getByRole("link", { name: "Articles" }).click();
    await expect(page).toHaveURL(/\/articles$/);

    // Heading & subtitle
    await expect(
      page.getByRole("heading", { name: "Recent Articles" })
    ).toBeVisible();
    await expect(
      page.getByText(/Latest cryptocurrency news/, { exact: false })
    ).toBeVisible();

    // Ingestion controls present
    const sources = [/DL News/i, /The Defiant/i, /Cointelegraph/i];
    for (const source of sources) {
      await expect(
        page.getByRole("button", {
          name: new RegExp(`Ingest .*${source.source}`, "i"),
        })
      ).toBeVisible();
    }

    // Optionally verify one of the dynamic table states; do not fail if absent
    const possibleSelectors = [
      page.getByText(/Loading news articles/i),
      page.getByText(/No news articles found/i),
      page.getByText(/Error loading news/i),
      page.getByRole("columnheader", { name: "Title" }),
    ];

    for (const locator of possibleSelectors) {
      if (
        await locator
          .first()
          .isVisible()
          .catch(() => false)
      ) {
        // Found a visible state; stop checking further
        break;
      }
    }
  });
});
