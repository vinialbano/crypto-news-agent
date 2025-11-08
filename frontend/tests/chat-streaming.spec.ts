import { test, expect } from "@playwright/test";

/**
 * Chat streaming test (WebSocket-based):
 * - Loads homepage Chat view
 * - Sends a question
 * - Verifies the user message appears
 * - Verifies assistant starts streaming: shows Sources list and a placeholder ("Thinking...")
 * - Asserts input/send are disabled during streaming
 * - Verifies sources contain external links with proper target/rel
 */

test.describe("Chat streaming via WebSocket", () => {
  test("sends a message and observes streaming response", async ({ page }) => {
    await page.goto("/");

    // Basic Chat UI present
    await expect(page.getByRole("heading", { name: "Chat" })).toBeVisible();

    // Prepare question (keep idempotent and generic)
    const question =
      "Summarize the latest Bitcoin headlines from the articles list.";

    const input = page.getByPlaceholder("Ask about cryptocurrency news...");

    // Wait briefly for input to become enabled if the socket just connected
    await input.waitFor({ state: "visible" });

    // Fill and submit (Enter submits per component behavior)
    await input.fill(question);
    await page.keyboard.press("Enter");

    // User message echo appears
    await expect(page.getByText(question, { exact: false })).toBeVisible();

    // Assistant streaming starts: expect Sources section and/or Thinking placeholder
    // Prefer Sources since server emits them first
    await expect(page.getByText(/Sources \(\d+\):/)).toBeVisible({
      timeout: 30000,
    });

    // During streaming, the input and its submit button should be disabled (ignore devtool buttons)
    await expect(input).toBeDisabled();
    const submitButton = page.locator("form").getByRole("button");
    await expect(submitButton).toBeDisabled();

    // Verify at least one external link in sources with target/rel
    const links = page.locator('a[target="_blank"]');
    await expect(links.first()).toBeVisible();

    const count = Math.min(await links.count(), 5);
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
      const link = links.nth(i);
      const href = await link.getAttribute("href");
      const target = await link.getAttribute("target");
      const rel = await link.getAttribute("rel");
      expect(href).toBeTruthy();
      expect(href).toMatch(/^https?:\/\//);
      expect(target).toBe("_blank");
      expect((rel ?? "").toLowerCase()).toContain("noopener");
    }

    // Optional: indicator text while streaming
    await expect(page.getByText(/Thinking\.\.\./)).toBeVisible({
      timeout: 30000,
    });
  });
});
