export const errorTracker: {
  init: () => void
  handleVueError: (err: unknown, instance: any, info: string) => void
  captureException: (error: Error) => void
}
