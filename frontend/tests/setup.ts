/**
 * Vitest global setup file
 * Runs before all tests
 */

// Type definitions for mocks
interface MediaQueryList {
  matches: boolean
  media: string
  onchange: ((this: MediaQueryList, ev: MediaQueryListEvent) => unknown) | null
  addListener: (listener: () => void) => void
  removeListener: (listener: () => void) => void
  addEventListener: (type: string, listener: () => void) => void
  removeEventListener: (type: string, listener: () => void) => void
  dispatchEvent: (event: Event) => boolean
}

// Mock window.matchMedia for theme tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string): MediaQueryList => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: (): void => {}, // deprecated
    removeListener: (): void => {}, // deprecated
    addEventListener: (): void => {},
    removeEventListener: (): void => {},
    dispatchEvent: (): boolean => true
  })
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

// Mock localStorage
interface LocalStorageMock {
  [key: string]: string
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
  removeItem: (key: string) => void
  clear: () => void
}

const localStorageMock: LocalStorageMock = {
  getItem(key: string): string | null {
    return this[key] || null
  },
  setItem(key: string, value: string): void {
    this[key] = value.toString()
  },
  removeItem(key: string): void {
    delete this[key]
  },
  clear(): void {
    Object.keys(this).forEach(key => {
      if (key !== 'getItem' && key !== 'setItem' && key !== 'removeItem' && key !== 'clear') {
        delete this[key]
      }
    })
  }
}

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
