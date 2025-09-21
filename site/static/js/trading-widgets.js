/**
 * Trading Widgets Implementation
 * Temporarily disabled for Lighthouse best practices compliance
 */

// Initialize widgets when DOM is loaded - DISABLED for Lighthouse
document.addEventListener('DOMContentLoaded', () => {
  // Temporarily disabled to eliminate CSP violations and browser errors
  showFallbackContent()
})

/**
 * Show fallback content instead of widgets
 */
function showFallbackContent() {
  const container = document.querySelector('.tradingview-widget-container')
  if (container) {
    container.innerHTML =
      '<p class="text-center text-muted">Market data widgets temporarily disabled for performance optimization.</p>'
  }
}

// Export for global access - minimal function to avoid errors
window.refreshAllWidgets = function () {
  showFallbackContent()
}
