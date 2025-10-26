export const analytics: {
  init: () => void
  trackPageView: (path: string, name?: string) => void
  trackEvent: (category: string, action: string, label?: string, value?: number) => void
}
