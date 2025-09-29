/**
 * Jest Test Setup
 * Global test environment configuration and utilities
 */

/* eslint-env jest, node */

// Fix for JSDOM TextEncoder issue
const { TextEncoder, TextDecoder } = require('util')
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock DOM APIs that JSDOM doesn't implement
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback, options) {
    this.callback = callback
    this.options = options
  }

  observe() {
    // Mock implementation
  }

  unobserve() {
    // Mock implementation
  }

  disconnect() {
    // Mock implementation
  }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {
    this.callback = callback
  }

  observe() {
    // Mock implementation
  }

  unobserve() {
    // Mock implementation
  }

  disconnect() {
    // Mock implementation
  }
}

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
}

// Override both global and window localStorage
Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true
})
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
}

// Override both global and window sessionStorage
Object.defineProperty(global, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true
})
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true
})

// Mock window.location
delete window.location
window.location = {
  href: 'http://localhost:3000',
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  pathname: '/',
  search: '',
  hash: '',
  reload: jest.fn(),
  replace: jest.fn(),
  assign: jest.fn()
}

// Mock window.history
Object.defineProperty(window, 'history', {
  writable: true,
  value: {
    pushState: jest.fn(),
    replaceState: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    go: jest.fn()
  }
})

// Mock window.scrollTo
window.scrollTo = jest.fn()

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16))
global.cancelAnimationFrame = jest.fn(clearTimeout)

// Mock fetch for API tests
global.fetch = jest.fn()

beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks()

  // Reset localStorage and sessionStorage with default return values
  localStorageMock.getItem.mockClear()
  localStorageMock.setItem.mockClear()
  localStorageMock.removeItem.mockClear()
  localStorageMock.clear.mockClear()

  // Default localStorage.getItem to return null
  localStorageMock.getItem.mockReturnValue(null)

  sessionStorageMock.getItem.mockClear()
  sessionStorageMock.setItem.mockClear()
  sessionStorageMock.removeItem.mockClear()
  sessionStorageMock.clear.mockClear()

  // Default sessionStorage.getItem to return null
  sessionStorageMock.getItem.mockReturnValue(null)
})

afterEach(() => {
  // Clean up DOM
  document.body.innerHTML = ''
  document.head.innerHTML = ''

  // Reset window properties
  window.location.pathname = '/'
  window.location.search = ''
  window.location.hash = ''
})

// Test utilities
const TestUtils = {
  // Create a mock DOM element with Jest spies
  createMockElement: (tag = 'div', attributes = {}) => {
    const element = document.createElement(tag)
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key, value)
    })

    // Add Jest spies for commonly used methods with event handling
    const eventListeners = {}
    element.addEventListener = jest
      .fn()
      .mockImplementation((event, handler) => {
        if (!eventListeners[event]) {
          eventListeners[event] = []
        }
        eventListeners[event].push(handler)
      })
    element.removeEventListener = jest.fn()
    element.dispatchEvent = jest.fn().mockImplementation(event => {
      const handlers = eventListeners[event.type] || []
      handlers.forEach(handler => handler(event))
      return true
    })
    element.focus = jest.fn()
    element.blur = jest.fn()
    element.click = jest.fn()
    element.appendChild = jest.fn().mockImplementation(child => {
      // Mock appendChild without modifying the actual children property
      return child
    })
    element.removeChild = jest.fn()
    element.querySelector = jest.fn()
    element.querySelectorAll = jest.fn().mockReturnValue([])
    element.getBoundingClientRect = jest.fn().mockReturnValue({
      top: 0,
      left: 0,
      bottom: 0,
      right: 0,
      width: 0,
      height: 0
    })

    // Spy on classList methods (classList is read-only in JSDOM)
    element.classList.add = jest.fn(
      element.classList.add.bind(element.classList)
    )
    element.classList.remove = jest.fn(
      element.classList.remove.bind(element.classList)
    )
    element.classList.toggle = jest.fn(
      element.classList.toggle.bind(element.classList)
    )
    element.classList.contains = jest.fn(
      element.classList.contains.bind(element.classList)
    )
    element.classList.replace = jest.fn(
      element.classList.replace.bind(element.classList)
    )

    // Mock setAttribute and getAttribute with spies
    const originalSetAttribute = element.setAttribute.bind(element)
    const originalGetAttribute = element.getAttribute.bind(element)
    const originalRemoveAttribute = element.removeAttribute.bind(element)
    element.setAttribute = jest.fn().mockImplementation(originalSetAttribute)
    element.getAttribute = jest.fn().mockImplementation(originalGetAttribute)
    element.removeAttribute = jest
      .fn()
      .mockImplementation(originalRemoveAttribute)

    return element
  },

  // Simulate user click
  simulateClick: element => {
    const event = new MouseEvent('click', {
      bubbles: true,
      cancelable: true
    })
    element.dispatchEvent(event)
  },

  // Simulate keyboard press
  simulateKeyPress: (element, key) => {
    const event = new KeyboardEvent('keydown', {
      key,
      bubbles: true,
      cancelable: true
    })
    element.dispatchEvent(event)
  },

  // Wait for async operations
  waitFor: (conditionFn, timeout = 1000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now()
      const checkCondition = () => {
        if (conditionFn()) {
          resolve()
        } else if (Date.now() - startTime >= timeout) {
          reject(new Error('Timeout waiting for condition'))
        } else {
          setTimeout(checkCondition, 10)
        }
      }
      checkCondition()
    })
  },

  // Mock external script loading
  mockScriptLoad: src => {
    const script = document.createElement('script')
    script.src = src
    document.head.appendChild(script)
    setTimeout(() => script.dispatchEvent(new Event('load')), 0)
    return script
  }
}

module.exports = { TestUtils }
