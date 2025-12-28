/**
 * Theme Management Composable
 * Handles dark/light theme switching with localStorage persistence
 * and system preference detection
 */
import { useDark, useToggle } from '@vueuse/core'
import { watch, onScopeDispose, type Ref } from 'vue'
import { themeLogger } from '../utils/logger'

type ThemeMode = 'dark' | 'light' | 'system'

interface UseThemeReturn {
  isDark: Ref<boolean>
  toggleTheme: (value?: boolean) => boolean
  currentTheme: () => 'dark' | 'light'
  setTheme: (theme: ThemeMode) => void
}

export function useTheme(): UseThemeReturn {
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
  const stopWatcher = watch(isDark, (dark: boolean) => {
    themeLogger.log('Theme changed to:', dark ? 'dark' : 'light')

    // Dispatch custom event for components that need to react to theme changes
    window.dispatchEvent(
      new CustomEvent('theme-changed', {
        detail: { theme: dark ? 'dark' : 'light' }
      })
    )
  })

  // Clean up watcher when scope is disposed
  onScopeDispose(() => {
    stopWatcher()
  })

  // Get current theme as string
  const currentTheme = (): 'dark' | 'light' => (isDark.value ? 'dark' : 'light')

  // Set specific theme
  const setTheme = (theme: ThemeMode): void => {
    if (theme === 'dark') {
      isDark.value = true
    } else if (theme === 'light') {
      isDark.value = false
    } else if (theme === 'system') {
      // Reset to system preference
      localStorage.removeItem('portfolio-theme')
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      isDark.value = systemPrefersDark
    } else if (import.meta.env.DEV) {
      // Warn in development about invalid theme values
      console.warn(
        `[useTheme] Invalid theme value: "${theme}". Expected "dark", "light", or "system".`
      )
    }
  }

  return {
    isDark,
    toggleTheme,
    currentTheme,
    setTheme
  }
}
