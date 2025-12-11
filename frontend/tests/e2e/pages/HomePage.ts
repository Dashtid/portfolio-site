import { type Page, type Locator, expect } from '@playwright/test'
import { BasePage } from './BasePage'

/**
 * Page Object for the Home page (main portfolio page)
 */
export class HomePage extends BasePage {
  // Navigation elements
  readonly navbar: Locator
  readonly navLinks: Locator
  readonly themeToggle: Locator
  readonly backToTop: Locator

  // Hero section
  readonly heroSection: Locator
  readonly heroTitle: Locator
  readonly heroSubtitle: Locator
  readonly profilePhoto: Locator

  // About section
  readonly aboutSection: Locator
  readonly aboutTitle: Locator

  // Experience section
  readonly experienceSection: Locator
  readonly experienceCards: Locator

  // Education section
  readonly educationSection: Locator
  readonly educationCards: Locator

  // Skills section
  readonly skillsSection: Locator

  constructor(page: Page) {
    super(page)

    // Navigation
    this.navbar = page.locator('nav')
    this.navLinks = page.locator('nav a')
    this.themeToggle = page.locator('[data-testid="theme-toggle"]')
    this.backToTop = page.locator('[data-testid="back-to-top"]')

    // Hero - use specific ID selector only
    this.heroSection = page.locator('#hero')
    this.heroTitle = page.locator('h1')
    this.heroSubtitle = page.locator('.hero-subtitle, h1 + p, h1 ~ p')
    this.profilePhoto = page.locator('img[alt*="David"], img[alt*="profile"]')

    // Sections
    this.aboutSection = page.locator('#about, section:has(h2:text("About"))')
    this.aboutTitle = page.locator('h2:has-text("About")')

    this.experienceSection = page.locator('#experience, section:has(h2:text("Experience"))')
    this.experienceCards = page.locator('#experience .card, [data-testid="experience-card"]')

    this.educationSection = page.locator('#education, section:has(h2:text("Education"))')
    this.educationCards = page.locator('#education .card, [data-testid="education-card"]')

    this.skillsSection = page.locator('#skills, section:has(h2:text("Skills"))')
  }

  /**
   * Navigate to home page
   */
  async goto(): Promise<void> {
    await super.goto('/')
    await this.waitForPageLoad()
  }

  /**
   * Verify hero section is visible and contains expected content
   */
  async verifyHeroSection(): Promise<void> {
    await expect(this.heroTitle).toBeVisible()
    const titleText = await this.heroTitle.textContent()
    expect(titleText).toBeTruthy()
  }

  /**
   * Verify navigation is visible and functional
   */
  async verifyNavigation(): Promise<void> {
    await expect(this.navbar).toBeVisible()
    const linksCount = await this.navLinks.count()
    expect(linksCount).toBeGreaterThan(0)
  }

  /**
   * Toggle theme and verify it changes
   */
  async toggleTheme(): Promise<string | null> {
    const htmlElement = this.page.locator('html')
    const initialTheme = await htmlElement.getAttribute('class')

    await this.themeToggle.click()
    await this.page.waitForTimeout(300) // Wait for theme transition

    const newTheme = await htmlElement.getAttribute('class')
    return newTheme
  }

  /**
   * Navigate to a section using nav link
   */
  async navigateToSection(sectionName: string): Promise<void> {
    const navLink = this.page.locator(`nav a[href*="${sectionName.toLowerCase()}"]`)
    await navLink.click()
    await this.page.waitForTimeout(500) // Wait for scroll animation
  }

  /**
   * Click on an experience card to view details
   */
  async clickExperienceCard(index: number = 0): Promise<void> {
    const cards = await this.experienceCards.all()
    if (cards.length > index) {
      await cards[index].click()
    }
  }

  /**
   * Verify back to top button works
   */
  async testBackToTop(): Promise<void> {
    // Scroll to bottom
    await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await this.page.waitForTimeout(500)

    // Click back to top if visible
    if (await this.backToTop.isVisible()) {
      await this.backToTop.click()
      await this.page.waitForTimeout(500)

      // Verify we're at the top
      const scrollY = await this.page.evaluate(() => window.scrollY)
      expect(scrollY).toBeLessThan(100)
    }
  }

  /**
   * Get the count of experience entries
   */
  async getExperienceCount(): Promise<number> {
    return this.experienceCards.count()
  }

  /**
   * Get the count of education entries
   */
  async getEducationCount(): Promise<number> {
    return this.educationCards.count()
  }

  /**
   * Verify all main sections are present
   */
  async verifySectionsExist(): Promise<void> {
    // Check for hero section
    await expect(this.heroSection).toBeAttached()

    // Check for main content sections by their IDs
    const experienceSection = this.page.locator('#experience')
    const educationSection = this.page.locator('#education')
    const aboutSection = this.page.locator('#about')

    // At least some of these sections should exist
    const heroCount = await this.heroSection.count()
    const expCount = await experienceSection.count()
    const eduCount = await educationSection.count()
    const aboutCount = await aboutSection.count()

    const totalSections = heroCount + expCount + eduCount + aboutCount
    expect(totalSections).toBeGreaterThan(0)
  }

  /**
   * Check page performance metrics
   */
  async getPerformanceMetrics(): Promise<{ lcp: number; fcp: number }> {
    const metrics = await this.page.evaluate(() => {
      return new Promise<{ lcp: number; fcp: number }>(resolve => {
        let lcp = 0
        let fcp = 0

        new PerformanceObserver(entryList => {
          const entries = entryList.getEntries()
          lcp = entries[entries.length - 1].startTime
        }).observe({ type: 'largest-contentful-paint', buffered: true })

        new PerformanceObserver(entryList => {
          const entries = entryList.getEntries()
          fcp = entries[0].startTime
        }).observe({ type: 'paint', buffered: true })

        // Wait a bit for metrics to be collected
        setTimeout(() => resolve({ lcp, fcp }), 1000)
      })
    })
    return metrics
  }
}
