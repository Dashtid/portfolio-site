import { type Page, type Locator, expect } from '@playwright/test'

/**
 * Base Page Object class providing common functionality for all page objects.
 * Implements the Page Object Model pattern for E2E tests.
 */
export abstract class BasePage {
  protected readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  /**
   * Navigate to a specific path
   */
  async goto(path: string = '/'): Promise<void> {
    await this.page.goto(path)
  }

  /**
   * Wait for page to be fully loaded
   * Uses domcontentloaded instead of networkidle to avoid timeouts from API calls
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded')
    // Wait for Vue app to mount
    await this.page.waitForSelector('#app', { state: 'attached' })
  }

  /**
   * Get the current page title
   */
  async getTitle(): Promise<string> {
    return this.page.title()
  }

  /**
   * Get the current URL
   */
  getUrl(): string {
    return this.page.url()
  }

  /**
   * Take a screenshot of the current page
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `tests/e2e/screenshots/${name}.png` })
  }

  /**
   * Wait for element to be visible
   */
  async waitForElement(selector: string): Promise<Locator> {
    const element = this.page.locator(selector)
    await element.waitFor({ state: 'visible' })
    return element
  }

  /**
   * Check if element is visible
   */
  async isElementVisible(selector: string): Promise<boolean> {
    const element = this.page.locator(selector)
    return element.isVisible()
  }

  /**
   * Scroll to element
   */
  async scrollToElement(selector: string): Promise<void> {
    const element = this.page.locator(selector)
    await element.scrollIntoViewIfNeeded()
  }

  /**
   * Wait for navigation to complete
   */
  async waitForNavigation(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded')
  }

  /**
   * Check accessibility of the current page
   */
  async checkAccessibility(): Promise<void> {
    // Basic accessibility checks
    // Check for main landmark
    const main = this.page.locator('main')
    await expect(main).toBeVisible()

    // Check for heading structure
    const h1 = this.page.locator('h1')
    await expect(h1).toBeVisible()

    // Check for skip link (if present)
    const skipLink = this.page.locator('a[href="#main-content"]')
    if ((await skipLink.count()) > 0) {
      await expect(skipLink).toBeAttached()
    }
  }

  /**
   * Check that page has no console errors
   */
  async checkNoConsoleErrors(): Promise<string[]> {
    const errors: string[] = []
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })
    return errors
  }

  /**
   * Get all links on the page
   */
  async getAllLinks(): Promise<string[]> {
    const links = await this.page.locator('a[href]').all()
    const hrefs: string[] = []
    for (const link of links) {
      const href = await link.getAttribute('href')
      if (href) {
        hrefs.push(href)
      }
    }
    return hrefs
  }
}
