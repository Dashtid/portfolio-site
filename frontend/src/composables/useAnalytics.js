/**
 * Analytics composable for easy integration in Vue components
 */
import { analytics, trackEvent, trackPageView, trackOutboundLink } from '@/utils/analytics'

export function useAnalytics() {
  /**
   * Track a custom event
   */
  const track = (eventName, props = {}) => {
    trackEvent(eventName, props)
  }

  /**
   * Track navigation events
   */
  const trackNavigation = (section) => {
    track('Navigation Click', { section })
  }

  /**
   * Track theme toggle
   */
  const trackThemeToggle = (theme) => {
    track('Theme Toggle', { theme })
  }

  /**
   * Track button clicks
   */
  const trackButtonClick = (buttonName, location = '') => {
    track('Button Click', { button: buttonName, location })
  }

  /**
   * Track external link clicks
   */
  const trackExternalLink = (url, label = '') => {
    trackOutboundLink(url)
    if (label) {
      track('External Link', { url, label })
    }
  }

  /**
   * Track contact interactions
   */
  const trackContact = (method) => {
    track('Contact', { method })
  }

  /**
   * Track project interactions
   */
  const trackProject = (action, projectName) => {
    track('Project Interaction', { action, project: projectName })
  }

  /**
   * Track scroll interactions
   */
  const trackScroll = (section) => {
    track('Scroll To', { section })
  }

  /**
   * Track GitHub stats view
   */
  const trackGitHubStats = (username) => {
    track('GitHub Stats Viewed', { username })
  }

  /**
   * Track back to top button
   */
  const trackBackToTop = () => {
    track('Back To Top')
  }

  return {
    analytics,
    track,
    trackNavigation,
    trackThemeToggle,
    trackButtonClick,
    trackExternalLink,
    trackContact,
    trackProject,
    trackScroll,
    trackGitHubStats,
    trackBackToTop,
    trackPageView
  }
}
