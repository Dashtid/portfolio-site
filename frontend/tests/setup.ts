/**
 * Vitest global setup file
 * Runs before all tests
 */

// Mock script loading to prevent happy-dom errors
// happy-dom throws when a script element with src is appended to DOM
// We intercept appendChild on head/body to prevent script loading while preserving DOM structure
const preventScriptLoad = (element: Element): void => {
  if (element.tagName === 'SCRIPT' && element.hasAttribute('src')) {
    // Remove src temporarily, append, then restore as attribute only
    const src = element.getAttribute('src')
    element.removeAttribute('src')
    // Use a data attribute to preserve the src value for test assertions
    if (src) {
      element.setAttribute('data-test-src', src)
      // Also set a non-loading attribute version
      Object.defineProperty(element, 'src', {
        get: () => src,
        set: () => {},
        configurable: true
      })
      // Restore src attribute for querySelector compatibility
      element.setAttribute('src', src)
    }
  }
}

// Wrap appendChild on head and body
const originalHeadAppendChild = HTMLHeadElement.prototype.appendChild
HTMLHeadElement.prototype.appendChild = function <T extends Node>(node: T): T {
  if (node instanceof Element) {
    preventScriptLoad(node)
  }
  return originalHeadAppendChild.call(this, node)
}

const originalBodyAppendChild = HTMLBodyElement.prototype.appendChild
HTMLBodyElement.prototype.appendChild = function <T extends Node>(node: T): T {
  if (node instanceof Element) {
    preventScriptLoad(node)
  }
  return originalBodyAppendChild.call(this, node)
}

// Mock window.matchMedia for theme tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string): MediaQueryList =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: (): void => {}, // deprecated
      removeListener: (): void => {}, // deprecated
      addEventListener: (): void => {},
      removeEventListener: (): void => {},
      dispatchEvent: (): boolean => true
    }) as MediaQueryList
})

// Mock IntersectionObserver for scroll animations
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null
  readonly rootMargin: string = ''
  readonly thresholds: ReadonlyArray<number> = []

  constructor(_callback: IntersectionObserverCallback, _options?: IntersectionObserverInit) {}

  disconnect(): void {}
  observe(_target: Element): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
  unobserve(_target: Element): void {}
}

global.IntersectionObserver = MockIntersectionObserver

// Mock requestAnimationFrame
global.requestAnimationFrame = (cb: FrameRequestCallback): number => {
  return setTimeout(() => cb(performance.now()), 0) as unknown as number
}
global.cancelAnimationFrame = (id: number): void => {
  clearTimeout(id)
}

// Mock localStorage using a class to avoid index signature conflicts
class LocalStorageMock implements Storage {
  private store: Record<string, string> = {}

  get length(): number {
    return Object.keys(this.store).length
  }

  key(index: number): string | null {
    const keys = Object.keys(this.store)
    return keys[index] || null
  }

  getItem(key: string): string | null {
    return this.store[key] ?? null
  }

  setItem(key: string, value: string): void {
    this.store[key] = value.toString()
  }

  removeItem(key: string): void {
    delete this.store[key]
  }

  clear(): void {
    this.store = {}
  }
}

const localStorageMock = new LocalStorageMock()

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true
})

// Mock console methods to reduce test output noise
const originalConsole = { ...console }
global.console = {
  ...originalConsole,
  log: (): void => {}, // suppress console.log
  debug: (): void => {}, // suppress console.debug
  info: (): void => {}, // suppress console.info
  // Keep warn and error for debugging
  warn: originalConsole.warn,
  error: originalConsole.error
}
