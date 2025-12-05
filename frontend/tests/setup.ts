/**
 * Vitest global setup file
 * Runs before all tests
 */

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
