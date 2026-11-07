import { test, expect } from '@playwright/test'
import path from 'node:path'
const fixtures = path.resolve(import.meta.dirname, '../../fixtures')
test('before and after import, actionable error, approval, replay and registry', async ({
  page,
}) => {
  const errors: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Admissions imports', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Before · strict parser' }).click()
  await page.getByLabel('Upload admissions CSV').setInputFiles(path.join(fixtures, 'atlas_v1.csv'))
  await expect(page.getByTestId('record-count')).toHaveText('3unique identities')
  await page.getByLabel('Upload admissions CSV').setInputFiles(path.join(fixtures, 'atlas_v2.csv'))
  await expect(
    page
      .getByRole('table', { name: 'Import history' })
      .getByText('Schema rejected', { exact: true }),
  ).toBeVisible()
  await page.screenshot({ path: '../evidence/01-baseline.png', fullPage: true })
  await page.getByRole('button', { name: 'After · safer mappings' }).click()
  await page.getByRole('button', { name: 'Import sample' }).click()
  await expect(page.getByTestId('record-count')).toHaveText('3unique identities')
  await expect(
    page
      .getByRole('table', { name: 'Validation errors' })
      .getByText('student_key', { exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('table', { name: 'Accepted rows' }).getByText('waitlisted', { exact: true }),
  ).toBeVisible()
  await page.screenshot({ path: '../evidence/02-normalized.png', fullPage: true })
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download report' }).click()
  await expect((await download).suggestedFilename()).toMatch(/import-\d+-report.json/)
  await page
    .getByLabel('Upload admissions CSV')
    .setInputFiles(path.join(fixtures, 'ambiguous_v3.csv'))
  await expect(
    page.getByRole('heading', { name: 'Resolve the schema before importing' }),
  ).toBeVisible()
  await expect(page.getByLabel('Application year', { exact: true })).toHaveValue('')
  await expect(page.getByRole('button', { name: 'Approve mapping & import' })).toBeDisabled()
  await page.screenshot({ path: '../evidence/03-quarantine.png', fullPage: true })
  await page.getByLabel('Application year', { exact: true }).selectOption('application_year')
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Approve mapping & import' }).click()
  await expect(page.getByTestId('record-count')).toHaveText('5unique identities')
  await expect(page.getByRole('status')).toContainText('2 inserted')
  await expect(
    page.getByRole('table', { name: 'Accepted rows' }).getByText('2029', { exact: true }),
  ).toHaveCount(0)
  await page
    .getByLabel('Upload admissions CSV')
    .setInputFiles(path.join(fixtures, 'ambiguous_v3.csv'))
  await expect(page.getByRole('status')).toContainText('Exact file replay')
  await expect(page.getByTestId('record-count')).toHaveText('5unique identities')
  await page.screenshot({ path: '../evidence/04-approved-replay.png', fullPage: true })
  await page.getByRole('button', { name: 'Mapping registry' }).click()
  await expect(page.getByRole('heading', { name: 'Mapping registry', exact: true })).toBeVisible()
  await expect(page.getByText('Atlas review@1 · Demo operator', { exact: false })).toBeVisible()
  await page.screenshot({ path: '../evidence/05-registry.png', fullPage: true })
  expect(errors).toEqual([])
})

test('mobile layout and unknown schema stay reviewable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByLabel('Synthetic vendor fixture').selectOption('unknown_v1.csv')
  await page.getByRole('button', { name: 'Import sample' }).click()
  await expect(
    page.getByRole('heading', { name: 'Resolve the schema before importing' }),
  ).toBeVisible()
  await expect(
    page
      .getByRole('table', { name: 'Validation errors' })
      .getByText('No recognized header; select a source column.'),
  ).toHaveCount(2)
  await expect(page.getByRole('button', { name: 'Approve mapping & import' })).toBeDisabled()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.screenshot({ path: '../evidence/06-mobile.png', fullPage: true })
})
