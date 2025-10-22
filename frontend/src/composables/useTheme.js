/**
 * Theme Management Composable
 * Handles dark/light theme switching with localStorage persistence
 * and system preference detection
 */
import { useDark, useToggle } from '@vueuse/core'
import { watch } from 'vue'

export function useTheme() {
  // useDark automatically:
  // - Detects system preference (prefers-color-scheme)
  // - Persists to localStorage
  // - Updates DOM attribute data-theme on <html>
  const isDark = useDark({
    storageKey: 'portfolio-theme',
    valueDark: 'dark',
    valueLight: 'light',
    attribute: 'data-theme',
    selector: 'html'
  })

  const toggleTheme = useToggle(isDark)

  // Watch for theme changes to update icon variants
  watch(isDark, (dark) => {
    console.log('[Theme] Theme changed to:', dark ? 'dark' : 'light')

    // Dispatch custom event for components that need to react to theme changes
    window.dispatchEvent(new CustomEvent('theme-changed', {
      detail: { theme: dark ? 'dark' : 'light' }
    }))
  })

  // Get current theme as string
  const currentTheme = () => isDark.value ? 'dark' : 'light'

  // Set specific theme
  const setTheme = (theme) => {
    if (theme === 'dark') {
      isDark.value = true
    } else if (theme === 'light') {
      isDark.value = false
    } else if (theme === 'system') {
      // Reset to system preference
      localStorage.removeItem('portfolio-theme')
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      isDark.value = systemPrefersDark
    }
  }

  return {
    isDark,
    toggleTheme,
    currentTheme,
    setTheme
  }
}
