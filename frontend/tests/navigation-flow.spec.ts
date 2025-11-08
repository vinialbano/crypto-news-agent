import { test, expect } from "@playwright/test";

/**
 * Navigation flow test:
 * 1. Start at homepage (baseURL '/')
 * 2. Assert navbar brand & links visible
 * 3. Assert Chat header & welcome copy
 * 4. Navigate to Articles page via navbar link
 * 5. Assert Articles heading, ingestion buttons, table headers
 * 6. Navigate back to Chat
 */

test.describe("Primary navigation flow", () => {
  test("chat -> articles -> chat", async ({ page }) => {
    // Step 1: Start at homepage
    await page.goto("/");

    // Step 2: Navbar basics
    await expect(
      page.getByRole("link", { name: "Crypto News Agent" })
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "Chat" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Articles" })).toBeVisible();

    // Step 3: Chat landing content
    await expect(page.getByRole("heading", { name: "Chat" })).toBeVisible();
    await expect(page.getByText(/Welcome to Crypto News Chat!/)).toBeVisible();
    // Connection badge can vary; assert presence of any known state label
    await expect(
      page.getByText(/Connected|Connecting|Disconnected|Error/) // dynamic
    ).toBeVisible();

    // Step 4: Navigate to Articles
    await page.getByRole("link", { name: "Articles" }).click();
    await expect(page).toHaveURL(/\/articles$/);

    // Step 5: Articles page assertions
    await expect(
      page.getByRole("heading", { name: "Recent Articles" })
    ).toBeVisible();
    for (const source of ["DL News", "The Defiant", "Cointelegraph"]) {
      await expect(
        page.getByRole("button", { name: new RegExp(`Ingest ${source}`, "i") })
      ).toBeVisible();
    }
    // Verify articles table/state in a resilient way (accept different states)
    const candidates = [
      page.getByRole("button", { name: "Title" }).first(),
      page.getByRole("button", { name: "Published" }).first(),
      page.getByText(/Showing \d+ to \d+ of \d+ articles/i),
      page.locator("table tbody tr").first(),
      page.getByText(/No news articles found/i),
      page.getByText(/Loading news articles/i),
    ];
    let stateFound = false;
    for (const loc of candidates) {
      if (await loc.isVisible().catch(() => false)) {
        stateFound = true;
        break;
      }
    }
    expect(stateFound).toBeTruthy();

    // Step 6: Back to Chat
    await page.getByRole("link", { name: "Chat" }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "Chat" })).toBeVisible();
  });
});
