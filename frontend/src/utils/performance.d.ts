export const performanceMonitor: {
  init: () => void
  mark: (name: string) => void
  measure: (name: string, startMark: string, endMark: string) => void
}
