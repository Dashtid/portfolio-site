import { ref, nextTick, onUnmounted, type Ref } from 'vue'

/**
 * Composable for trapping focus within a container element (WCAG 2.2 compliant)
 * Used for modal dialogs, drawers, and other overlay components
 */
export function useFocusTrap(containerRef: Ref<HTMLElement | null>) {
  const previousActiveElement = ref<HTMLElement | null>(null)

  const FOCUSABLE_SELECTORS = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable]'
  ].join(', ')

  function getFocusableElements(): HTMLElement[] {
    if (!containerRef.value) return []
    return Array.from(containerRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS))
  }

  function handleKeyDown(event: KeyboardEvent): void {
    if (event.key !== 'Tab') return

    const focusableElements = getFocusableElements()
    if (focusableElements.length === 0) return

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    if (event.shiftKey) {
      // Shift+Tab: if on first element, wrap to last
      if (document.activeElement === firstElement) {
        event.preventDefault()
        lastElement.focus()
      }
    } else {
      // Tab: if on last element, wrap to first
      if (document.activeElement === lastElement) {
        event.preventDefault()
        firstElement.focus()
      }
    }
  }

  function activate(): void {
    // Store currently focused element to restore later
    previousActiveElement.value = document.activeElement as HTMLElement

    // Add keydown listener for focus trapping
    document.addEventListener('keydown', handleKeyDown)

    // Focus first focusable element
    nextTick(() => {
      const focusableElements = getFocusableElements()
      if (focusableElements.length > 0) {
        focusableElements[0].focus()
      }
    })
  }

  function deactivate(): void {
    // Remove keydown listener
    document.removeEventListener('keydown', handleKeyDown)

    // Restore focus to previous element
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }

  // Clean up on unmount
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })

  return {
    activate,
    deactivate
  }
}
