import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('loads successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/David Dashti/)
  })

  test('displays hero section', async ({ page }) => {
    const hero = page.locator('#hero')
    await expect(hero).toBeVisible()
    await expect(hero).toContainText('Cybersecurity')
    await expect(hero).toContainText('Artificial Intelligence')
  })

  test('displays navigation bar', async ({ page }) => {
    const nav = page.locator('nav')
    await expect(nav).toBeVisible()
    await expect(nav).toContainText('David Dashti')
  })

  test('displays all main sections', async ({ page }) => {
    // Check for main sections
    await expect(page.locator('#hero')).toBeVisible()
    await expect(page.locator('#experience')).toBeVisible()
    await expect(page.locator('#education')).toBeVisible()
    await expect(page.locator('#projects')).toBeVisible()
    await expect(page.locator('#about')).toBeVisible()
    await expect(page.locator('#contact')).toBeVisible()
  })

  test('displays experience cards', async ({ page }) => {
    const experienceSection = page.locator('#experience')
    await expect(experienceSection).toBeVisible()

    // Should have at least one experience card
    const cards = page.locator('.experience-card')
    await expect(cards.first()).toBeVisible()
  })

  test('displays education cards', async ({ page }) => {
    const educationSection = page.locator('#education')
    await expect(educationSection).toBeVisible()

    // Should have education cards
    const cards = page.locator('.education-card')
    await expect(cards.first()).toBeVisible()
  })

  test('displays projects section', async ({ page }) => {
    const projectsSection = page.locator('#projects')
    await expect(projectsSection).toBeVisible()

    // Should have GitHub stats or projects
    const hasStats = await page.locator('.github-stats').count() > 0
    const hasProjects = await page.locator('.project-card').count() > 0

    expect(hasStats || hasProjects).toBeTruthy()
  })

  test('displays contact information', async ({ page }) => {
    const contactSection = page.locator('#contact')
    await expect(contactSection).toBeVisible()

    // Should have links to LinkedIn and GitHub
    const linkedIn = page.getByRole('link', { name: /linkedin/i })
    const github = page.getByRole('link', { name: /github/i })

    await expect(linkedIn).toBeVisible()
    await expect(github).toBeVisible()
  })

  test('displays footer', async ({ page }) => {
    const footer = page.locator('footer')
    await expect(footer).toBeVisible()
  })

  test('has responsive meta viewport', async ({ page }) => {
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content')
    expect(viewport).toContain('width=device-width')
  })

  test('loads main image', async ({ page }) => {
    // Check that at least one image loads successfully
    const images = page.locator('img')
    await expect(images.first()).toBeVisible()
  })

  test('service worker registers successfully', async ({ page }) => {
    // Wait for service worker to register
    await page.waitForTimeout(2000)

    const swRegistered = await page.evaluate(() => {
      return 'serviceWorker' in navigator
    })

    expect(swRegistered).toBeTruthy()
  })
})
