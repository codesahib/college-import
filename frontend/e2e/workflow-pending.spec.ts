import { test, expect } from '@playwright/test'

test('pending baseline import prevents workflow switch and keeps matching detail', async ({ page }) => {
  let release!: () => void
  let arrived!: () => void
  const held = new Promise<void>((resolve) => (release = resolve))
  const entered = new Promise<void>((resolve) => (arrived = resolve))
  await page.route('**/api/imports?workflow=baseline', async (route) => {
    arrived()
    await held
    await route.continue()
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Before · strict parser' }).click()
  await page.getByRole('button', { name: 'Import sample' }).click()
  await entered
  try {
    const after = page.getByRole('button', { name: 'After · safer mappings' })
    // A DOM click attempts switching even while disabled; disabled controls must ignore it.
    await after.evaluate((button) => (button as HTMLButtonElement).click())
    await expect(after).toBeDisabled()
    await expect(page.locator('.segmented .chosen')).toHaveText('Before · strict parser')
  } finally {
    release()
  }
  await expect(page.getByRole('region', { name: 'Import detail' })).toContainText('BASELINE')
  const after = page.getByRole('button', { name: 'After · safer mappings' })
  await expect(after).toBeEnabled()
  await after.click()
  await expect(page.locator('.segmented .chosen')).toHaveText('After · safer mappings')
  await expect(page.getByRole('region', { name: 'Import detail' })).toHaveCount(0)
})
