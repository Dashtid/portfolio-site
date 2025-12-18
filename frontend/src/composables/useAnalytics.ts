/**
 * Analytics composable for easy integration in Vue components
 */
import { analytics, trackEvent, trackPageView, trackOutboundLink } from '@/utils/analytics'

interface TrackingProps {
  [key: string]: string | number | boolean | undefined
}

export function useAnalytics() {
  /**
   * Track a custom event
   * Wrapped in try-catch to prevent analytics errors from crashing the app
   */
  const track = (eventName: string, props: TrackingProps = {}): void => {
    try {
      trackEvent(eventName, props)
    } catch (error) {
      console.warn('[Analytics] Failed to track event:', eventName, error)
    }
  }

  /**
   * Track navigation events
   */
  const trackNavigation = (section: string): void => {
    track('Navigation Click', { section })
  }

  /**
   * Track theme toggle
   */
  const trackThemeToggle = (theme: string): void => {
    track('Theme Toggle', { theme })
  }

  /**
   * Track button clicks
   */
  const trackButtonClick = (buttonName: string, location: string = ''): void => {
    track('Button Click', { button: buttonName, location })
  }

  /**
   * Track external link clicks
   */
  const trackExternalLink = (url: string, label: string = ''): void => {
    try {
      trackOutboundLink(url)
    } catch (error) {
      console.warn('[Analytics] Failed to track outbound link:', url, error)
    }
    if (label) {
      track('External Link', { url, label })
    }
  }

  /**
   * Track contact interactions
   */
  const trackContact = (method: string): void => {
    track('Contact', { method })
  }

  /**
   * Track project interactions
   */
  const trackProject = (action: string, projectName: string): void => {
    track('Project Interaction', { action, project: projectName })
  }

  /**
   * Track scroll interactions
   */
  const trackScroll = (section: string): void => {
    track('Scroll To', { section })
  }

  /**
   * Track GitHub stats view
   */
  const trackGitHubStats = (username: string): void => {
    track('GitHub Stats Viewed', { username })
  }

  /**
   * Track back to top button
   */
  const trackBackToTop = (): void => {
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
