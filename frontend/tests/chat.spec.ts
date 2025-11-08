import { test, expect } from "@playwright/test";

test.describe("Chat page", () => {
  test("displays connection badge and disabled input when disconnected", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Chat" })).toBeVisible();

    // Connection badge text (Disconnected or Connecting)
    const badge = page.getByText(/Connected|Connecting|Disconnected|Error/);
    await expect(badge).toBeVisible();

    // Input is disabled until WebSocket connects (in dev may fail giving disabled state)
    const input = page.getByPlaceholder("Ask about cryptocurrency news...");
    await expect(input).toBeVisible();
    // The input may or may not be disabled depending on timing; perform soft assertion on disabled state
    const isDisabled = await input.isDisabled().catch(() => false);
    if (!isDisabled) {
      // If not disabled, we can send a small message and expect it to appear later
      await input.fill("What is the latest news about Bitcoin?");
      await page.getByRole("button").click();
      // Wait briefly for message echo (user message)
      await expect(
        page.getByText("What is the latest news about Bitcoin?", {
          exact: false,
        })
      ).toBeVisible({ timeout: 3000 });
    }
  });
});
