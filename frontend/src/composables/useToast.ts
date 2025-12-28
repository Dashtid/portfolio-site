/**
 * Toast Notification Composable
 * Provides non-blocking notifications to replace browser alert() dialogs
 */
import { ref, readonly, type Ref, type DeepReadonly } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: number
  message: string
  type: ToastType
  duration: number
}

interface UseToastReturn {
  toasts: DeepReadonly<Ref<Toast[]>>
  success: (message: string, duration?: number) => void
  error: (message: string, duration?: number) => void
  warning: (message: string, duration?: number) => void
  info: (message: string, duration?: number) => void
  remove: (id: number) => void
  clear: () => void
}

// Shared state across all instances
const toasts = ref<Toast[]>([])
let nextId = 0

// Default durations (ms)
const DEFAULT_DURATION = 4000
const ERROR_DURATION = 6000

/**
 * Toast notification composable
 * Usage:
 *   const toast = useToast()
 *   toast.success('Company saved!')
 *   toast.error('Failed to save')
 */
export function useToast(): UseToastReturn {
  const addToast = (message: string, type: ToastType, duration: number): void => {
    const id = nextId++
    const toast: Toast = { id, message, type, duration }
    toasts.value = [...toasts.value, toast]

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }
  }

  const success = (message: string, duration = DEFAULT_DURATION): void => {
    addToast(message, 'success', duration)
  }

  const error = (message: string, duration = ERROR_DURATION): void => {
    addToast(message, 'error', duration)
  }

  const warning = (message: string, duration = DEFAULT_DURATION): void => {
    addToast(message, 'warning', duration)
  }

  const info = (message: string, duration = DEFAULT_DURATION): void => {
    addToast(message, 'info', duration)
  }

  const remove = (id: number): void => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const clear = (): void => {
    toasts.value = []
  }

  return {
    toasts: readonly(toasts),
    success,
    error,
    warning,
    info,
    remove,
    clear
  }
}

export default useToast
