// Type declarations for JavaScript service modules

declare module './analytics' {
  const analytics: {
    trackPageView: (path: string, name?: string) => void
  }
  export default analytics
}
