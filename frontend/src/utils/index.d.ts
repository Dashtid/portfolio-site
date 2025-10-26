// Type declarations for JavaScript utility modules

declare module './analytics' {
  export const analytics: {
    init: () => void
    trackPageView: (path: string, name?: string) => void
    trackEvent: (category: string, action: string, label?: string, value?: number) => void
  }
}

declare module './errorTracking' {
  export const errorTracker: {
    init: () => void
    handleVueError: (err: unknown, instance: any, info: string) => void
    captureException: (error: Error) => void
  }
}

declare module './performance' {
  export const performanceMonitor: {
    init: () => void
    mark: (name: string) => void
    measure: (name: string, startMark: string, endMark: string) => void
  }
}
