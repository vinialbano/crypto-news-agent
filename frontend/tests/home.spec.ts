import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test('loads and shows Chat landing content', async ({ page }) => {
    await page.goto('/')

    // Basic document checks
    await expect(page).toHaveTitle(/Crypto News Agent/i)

    // Navbar links
    await expect(page.getByRole('link', { name: 'Chat' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Articles' })).toBeVisible()

    // Chat header and welcome copy
    await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()
    await expect(
      page.getByText('Welcome to Crypto News Chat!', { exact: false })
    ).toBeVisible()
  })
})
