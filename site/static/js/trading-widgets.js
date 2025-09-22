/**
 * Original Working TradingView Widgets Implementation
 * Restoring your original market-overview widget from commit 420b707
 */

// Initialize widgets when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  initializeTradingWidgets()
})

/**
 * Initialize all trading widgets on the page
 */
function initializeTradingWidgets() {
  // Get current theme
  const theme = document.documentElement.getAttribute('data-theme') || 'light'
  const widgetTheme = theme === 'dark' ? 'dark' : 'light'

  // Initialize home page widget (your original working config)
  initializeHomeWidget(widgetTheme)

  // Initialize market analysis widgets
  if (window.location.pathname.includes('market-analysis')) {
    initializeMarketAnalysisWidgets(widgetTheme)
  }

  // Listen for theme changes
  observeThemeChanges()
}

/**
 * Initialize the original single world index widget
 * Large, simple widget tracking just one world index - your original working config
 */
function initializeHomeWidget(theme) {
  const container = document.querySelector('.tradingview-widget-container')
  if (!container) return

  try {
    // Clear any existing scripts
    const existingScripts = container.querySelectorAll('script')
    existingScripts.forEach(script => script.remove())

    // Set container height for the big widget
    container.style.height = '500px'

    // Create and load script - Single Symbol Overview Widget for world index
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.src =
      'https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js'
    script.async = true

    // Configuration for single world index (MSCI World Index or S&P 500 Global)
    script.innerHTML = JSON.stringify({
      symbols: [
        ['FOREXCOM:SPXUSD', 'S&P 500'] // Major world index
      ],
      chartOnly: false,
      width: '100%',
      height: '500',
      locale: 'en',
      colorTheme: theme,
      autosize: true,
      showVolume: true,
      showMA: false,
      hideDateRanges: false,
      hideMarketStatus: false,
      hideSymbolLogo: false,
      scalePosition: 'right',
      scaleMode: 'Normal',
      fontFamily:
        '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
      fontSize: '10',
      noTimeScale: false,
      valuesTracking: '1',
      changeMode: 'price-and-percent',
      chartType: 'area',
      headerFontSize: 'medium',
      lineWidth: 2,
      lineType: 0,
      dateRanges: ['1d|1', '1m|30', '3m|60', '12m|1D', '60m|1W', 'all|1M']
    })

    container.appendChild(script)
  } catch (error) {
    console.warn('TradingView widget error:', error)
    showFallbackContent(container, 'Market data temporarily unavailable.')
  }
}

/**
 * Initialize widgets for market analysis page
 */
function initializeMarketAnalysisWidgets(theme) {
  // Market sections data
  const marketSections = [
    {
      id: 'Americas',
      title: 'Americas',
      desc: 'Main Americas indices and their 5Y performance',
      symbols: [
        ['FOREXCOM:DJI', 'Dow Jones'],
        ['FOREXCOM:SPXUSD', 'S&P 500'],
        ['FOREXCOM:NSXUSD', 'NASDAQ'],
        ['TSX:TSX', 'TSX Composite'],
        ['BMFBOVESPA:IBOV', 'Bovespa']
      ]
    },
    {
      id: 'Europe',
      title: 'Europe',
      desc: 'Main European indices and their 5Y performance',
      symbols: [
        ['FOREXCOM:UKXGBP', 'FTSE 100'],
        ['FOREXCOM:FRXEUR', 'CAC 40'],
        ['XETR:DAX', 'DAX'],
        ['FOREXCOM:SPXEUR', 'Euro Stoxx 50'],
        ['FOREXCOM:ESXEUR', 'Euro Stoxx 600']
      ]
    },
    {
      id: 'APAC',
      title: 'Asia-Pacific',
      desc: 'Main Asia-Pacific indices and their 5Y performance',
      symbols: [
        ['TVC:NI225', 'Nikkei 225'],
        ['HKEX:HSI', 'Hang Seng'],
        ['SSE:000001', 'Shanghai Composite'],
        ['ASX:XJO', 'ASX 200'],
        ['KRX:KOSPI', 'KOSPI']
      ]
    }
  ]

  // Create market sections
  const marketWidgetsContainer = document.getElementById('market-widgets')
  if (marketWidgetsContainer) {
    marketWidgetsContainer.innerHTML = ''
    marketSections.forEach(section => {
      const sectionElement = createMarketSection(section, theme)
      marketWidgetsContainer.appendChild(sectionElement)
    })
  }

  // Initialize MedTech widget
  const medtechSymbols = [
    ['NYSE:MDT', 'Medtronic'],
    ['NYSE:JNJ', 'Johnson & Johnson'],
    ['XETR:SHL', 'Siemens Healthineers'],
    ['NYSE:SYK', 'Stryker'],
    ['NYSE:PHG', 'Philips'],
    ['NASDAQ:GEHC', 'GE HealthCare'],
    ['NYSE:ABT', 'Abbott'],
    ['NYSE:BSX', 'Boston Scientific'],
    ['NYSE:BDX', 'Becton Dickinson'],
    ['NYSE:BAX', 'Baxter']
  ]

  const medtechContainer = document.getElementById('medtech-widget')
  if (medtechContainer) {
    createSymbolOverviewWidget(medtechContainer, medtechSymbols, theme)
  }

  // Initialize Nuclear Medicine widget
  const nuclearSymbols = [
    ['NASDAQ:GEHC', 'GE HealthCare'],
    ['XETR:SHL', 'Siemens Healthineers'],
    ['NYSE:PHG', 'Philips'],
    ['NASDAQ:CMLS', 'Curium Medical']
  ]

  const nuclearContainer = document.getElementById('nuclear-widget')
  if (nuclearContainer) {
    createSymbolOverviewWidget(nuclearContainer, nuclearSymbols, theme)
  }
}

/**
 * Create a market section with widget
 */
function createMarketSection(section, theme) {
  const sectionDiv = document.createElement('section')
  sectionDiv.className = 'mb-5'
  sectionDiv.innerHTML = `
    <h2 class="mb-3">${section.title}</h2>
    <p class="mb-4 text-muted">${section.desc}</p>
    <div class="widget-container-${section.id.toLowerCase()}"></div>
  `

  // Create widget in the container
  const widgetContainer = sectionDiv.querySelector(
    `.widget-container-${section.id.toLowerCase()}`
  )
  createSymbolOverviewWidget(widgetContainer, section.symbols, theme)

  return sectionDiv
}

/**
 * Create a symbol overview widget using direct embed
 */
function createSymbolOverviewWidget(container, symbols, theme) {
  if (!container) return

  try {
    // Clear container
    container.innerHTML = ''

    // Create widget container
    const widgetDiv = document.createElement('div')
    widgetDiv.className = 'tradingview-widget-container mb-4'
    widgetDiv.style.height = '500px'

    widgetDiv.innerHTML = `
      <div class="tradingview-widget-container__widget"></div>
      <div class="tradingview-widget-copyright">
        <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
          <span class="blue-text">Track all markets on TradingView</span>
        </a>
      </div>
    `

    // Create script element with error handling
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.src =
      'https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js'
    script.async = true
    script.crossOrigin = 'anonymous'

    // Add error handling
    script.onerror = function () {
      showFallbackContent(widgetDiv, 'Market data temporarily unavailable.')
    }

    script.innerHTML = JSON.stringify({
      symbols,
      chartOnly: false,
      width: '100%',
      height: '500',
      locale: 'en',
      colorTheme: theme,
      autosize: true,
      showVolume: true,
      showMA: false,
      hideDateRanges: false,
      hideMarketStatus: false,
      hideSymbolLogo: false,
      scalePosition: 'right',
      scaleMode: 'Normal',
      fontFamily:
        '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
      fontSize: '10',
      noTimeScale: false,
      valuesTracking: '1',
      changeMode: 'price-and-percent',
      chartType: 'area',
      maLineColor: '#2563eb',
      maLineWidth: 1,
      maLength: 9,
      headerFontSize: 'medium',
      lineWidth: 2,
      lineType: 0,
      dateRanges: ['1d|1', '1m|30', '3m|60', '12m|1D', '60m|1W', 'all|1M']
    })

    widgetDiv.appendChild(script)
    container.appendChild(widgetDiv)
  } catch (error) {
    showFallbackContent(container, 'Market data temporarily unavailable.')
  }
}

/**
 * Show fallback content when widgets fail
 */
function showFallbackContent(container, message) {
  if (container) {
    container.innerHTML = `<p class="text-center text-muted">${message}</p>`
  }
}

/**
 * Observe theme changes and reload widgets
 */
function observeThemeChanges() {
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (
        mutation.type === 'attributes' &&
        mutation.attributeName === 'data-theme'
      ) {
        // Reload page to refresh widgets with new theme
        setTimeout(() => {
          window.location.reload()
        }, 100)
      }
    })
  })

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  })
}

/**
 * Utility function to refresh all widgets
 */
function refreshAllWidgets() {
  window.location.reload()
}

// Export for global access
window.refreshAllWidgets = refreshAllWidgets
