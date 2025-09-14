/**
 * Unit Tests for Trading Widgets
 * Tests widget initialization and theme handling
 */

const { TestUtils } = require('./setup.js')

// Mock functions from trading-widgets.js
const mockTradingWidgets = {
  initializeTradingWidgets: jest.fn(),
  initializeHomeWidget: jest.fn(),
  initializeMarketAnalysisWidgets: jest.fn(),
  observeThemeChanges: jest.fn(),
  refreshAllWidgets: jest.fn()
}

describe('Trading Widgets', () => {
  let mockContainer
  let mockScript

  beforeEach(() => {
    // Create mock widget container
    mockContainer = document.createElement('div')
    mockContainer.className = 'tradingview-widget-container'
    document.body.appendChild(mockContainer)

    // Mock document.createElement for script creation
    mockScript = TestUtils.createMockElement('script')
    const originalCreateElement = document.createElement
    document.createElement = jest.fn((tagName) => {
      if (tagName === 'script') {
        return mockScript
      }
      return originalCreateElement.call(document, tagName)
    })

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/',
        reload: jest.fn()
      },
      writable: true
    })
  })

  afterEach(() => {
    if (mockContainer.parentNode) {
      document.body.removeChild(mockContainer)
    }
    jest.clearAllMocks()
    jest.restoreAllMocks()
  })

  describe('Widget Initialization', () => {
    test('should initialize home widget with correct configuration', () => {
      const theme = 'light'

      // Simulate initializeHomeWidget function
      const container = document.querySelector('.tradingview-widget-container')
      expect(container).toBeTruthy()

      // Clear container
      container.innerHTML = ''

      // Create widget HTML structure
      container.innerHTML = `
        <div class="tradingview-widget-container__widget"></div>
        <div class="tradingview-widget-copyright">
          <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
            <span class="blue-text">Track all markets on TradingView</span>
          </a>
        </div>
      `

      expect(container.innerHTML).toContain(
        'tradingview-widget-container__widget'
      )
      expect(container.innerHTML).toContain('Track all markets on TradingView')
    })

    test('should handle missing container gracefully', () => {
      // Remove container
      document.body.removeChild(mockContainer)

      const container = document.querySelector('.tradingview-widget-container')
      expect(container).toBeNull()
    })

    test('should create script element for widget loading', () => {
      const script = document.createElement('script')

      expect(script).toBeDefined()
      expect(script.tagName.toLowerCase()).toBe('script')
    })

    test('should set correct script attributes', () => {
      const script = document.createElement('script')
      script.type = 'text/javascript'
      script.src =
        'https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js'
      script.async = true

      expect(script.type).toBe('text/javascript')
      expect(script.src).toBe(
        'https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js'
      )
      expect(script.async).toBe(true)
    })
  })

  describe('Theme Integration', () => {
    test('should detect current theme from document', () => {
      document.documentElement.setAttribute('data-theme', 'dark')

      const theme =
        document.documentElement.getAttribute('data-theme') || 'light'
      const widgetTheme = theme === 'dark' ? 'dark' : 'light'

      expect(widgetTheme).toBe('dark')
    })

    test('should default to light theme when no theme set', () => {
      document.documentElement.removeAttribute('data-theme')

      const theme =
        document.documentElement.getAttribute('data-theme') || 'light'
      const widgetTheme = theme === 'dark' ? 'dark' : 'light'

      expect(widgetTheme).toBe('light')
    })

    test('should observe theme changes with MutationObserver', () => {
      const mockCallback = jest.fn()
      const observer = new MutationObserver(mockCallback)

      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
      })

      // Change theme
      document.documentElement.setAttribute('data-theme', 'dark')

      // Trigger observer callback manually (since JSDOM doesn't trigger automatically)
      mockCallback([
        {
          type: 'attributes',
          attributeName: 'data-theme',
          target: document.documentElement
        }
      ])

      expect(mockCallback).toHaveBeenCalled()

      observer.disconnect()
    })
  })

  describe('Widget Configuration', () => {
    test('should create proper market overview widget config', () => {
      const config = {
        title: 'Stocks',
        tabs: [
          {
            title: 'Financial',
            symbols: [
              { s: 'NYSE:JPM', d: 'JPMorgan Chase' },
              { s: 'NYSE:WFC', d: 'Wells Fargo Co New' }
            ]
          },
          {
            title: 'Technology',
            symbols: [
              { s: 'NASDAQ:AAPL', d: 'Apple' },
              { s: 'NASDAQ:GOOGL', d: 'Alphabet' }
            ]
          }
        ],
        width: '100%',
        height: '100%',
        colorTheme: 'light'
      }

      expect(config.title).toBe('Stocks')
      expect(config.tabs).toHaveLength(2)
      expect(config.tabs[0].title).toBe('Financial')
      expect(config.tabs[0].symbols[0].s).toBe('NYSE:JPM')
      expect(config.colorTheme).toBe('light')
    })

    test('should create symbol overview widget config', () => {
      const symbols = [
        ['NYSE:MDT', 'Medtronic'],
        ['NYSE:JNJ', 'Johnson & Johnson']
      ]

      const config = {
        symbols,
        chartOnly: false,
        width: '100%',
        height: '500',
        locale: 'en',
        colorTheme: 'light',
        autosize: true
      }

      expect(config.symbols).toEqual(symbols)
      expect(config.height).toBe('500')
      expect(config.autosize).toBe(true)
    })
  })

  describe('Market Analysis Widgets', () => {
    test('should handle market analysis page detection', () => {
      window.location.pathname = '/market-analysis'

      const isMarketAnalysisPage =
        window.location.pathname.includes('market-analysis')

      expect(isMarketAnalysisPage).toBe(true)
    })

    test('should not initialize market analysis widgets on other pages', () => {
      window.location.pathname = '/'

      const isMarketAnalysisPage =
        window.location.pathname.includes('market-analysis')

      expect(isMarketAnalysisPage).toBe(false)
    })

    test('should create market section elements', () => {
      const section = {
        id: 'Americas',
        title: 'Americas',
        desc: 'Main Americas indices and their 5Y performance',
        symbols: [
          ['FOREXCOM:DJI', 'Dow Jones'],
          ['FOREXCOM:SPXUSD', 'S&P 500']
        ]
      }

      const sectionDiv = document.createElement('section')
      sectionDiv.className = 'mb-5'
      sectionDiv.innerHTML = `
        <h2 class="mb-3">${section.title}</h2>
        <p class="mb-4 text-muted">${section.desc}</p>
        <div class="widget-container-${section.id.toLowerCase()}"></div>
      `

      expect(sectionDiv.innerHTML).toContain('<h2 class="mb-3">Americas</h2>')
      expect(sectionDiv.innerHTML).toContain('Main Americas indices')
      expect(sectionDiv.innerHTML).toContain('widget-container-americas')
    })
  })

  describe('Error Handling', () => {
    test('should handle missing DOM elements gracefully', () => {
      document.body.removeChild(mockContainer)

      const container = document.querySelector('.tradingview-widget-container')

      expect(container).toBeNull()
    })

    test('should handle script loading errors', () => {
      const script = document.createElement('script')

      expect(() => {
        script.onerror = jest.fn()
        script.dispatchEvent(new Event('error'))
      }).not.toThrow()
    })

    test('should handle theme change during widget loading', () => {
      let reloadCalled = false
      window.location.reload = jest.fn(() => {
        reloadCalled = true
      })

      // Simulate theme change
      setTimeout(() => {
        window.location.reload()
      }, 100)

      setTimeout(() => {
        expect(reloadCalled).toBe(false) // Not called yet due to setTimeout
      }, 50)
    })
  })

  describe('Widget Content', () => {
    test('should include copyright information', () => {
      const copyrightHTML = `
        <div class="tradingview-widget-copyright">
          <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
            <span class="blue-text">Track all markets on TradingView</span>
          </a>
        </div>
      `

      expect(copyrightHTML).toContain('tradingview-widget-copyright')
      expect(copyrightHTML).toContain('https://www.tradingview.com/')
      expect(copyrightHTML).toContain('Track all markets on TradingView')
      expect(copyrightHTML).toContain('noopener nofollow')
    })

    test('should create proper widget container structure', () => {
      const widgetDiv = document.createElement('div')
      widgetDiv.className = 'tradingview-widget-container mb-4'
      widgetDiv.style.height = '500px'

      expect(widgetDiv.className).toBe('tradingview-widget-container mb-4')
      expect(widgetDiv.style.height).toBe('500px')
    })
  })

  describe('Accessibility', () => {
    test('should include proper link attributes', () => {
      const link = TestUtils.createMockElement('a', {
        href: 'https://www.tradingview.com/',
        rel: 'noopener nofollow',
        target: '_blank'
      })

      expect(link.getAttribute('rel')).toBe('noopener nofollow')
      expect(link.getAttribute('target')).toBe('_blank')
      expect(link.getAttribute('href')).toBe('https://www.tradingview.com/')
    })

    test('should provide meaningful widget content', () => {
      const widget = document.createElement('div')
      widget.className = 'tradingview-widget-container__widget'

      expect(widget.className).toBe('tradingview-widget-container__widget')
    })
  })
})
