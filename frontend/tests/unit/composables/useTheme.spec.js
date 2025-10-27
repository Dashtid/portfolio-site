import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useTheme } from '@/composables/useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear()

    // Reset document theme
    document.documentElement.removeAttribute('data-theme')

    // Reset matchMedia mock
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn()
    }))
  })

  it('initializes with default theme', () => {
    const { isDark, currentTheme } = useTheme()

    expect(isDark).toBeDefined()
    expect(currentTheme).toBeDefined()
  })

  it('toggles theme', () => {
    const { isDark, toggleTheme } = useTheme()

    const initialValue = isDark.value
    toggleTheme()

    expect(isDark.value).toBe(!initialValue)
  })

  it('sets theme to light', () => {
    const { isDark, setTheme } = useTheme()

    setTheme('light')

    expect(isDark.value).toBe(false)
  })

  it('sets theme to dark', () => {
    const { isDark, setTheme } = useTheme()

    setTheme('dark')

    expect(isDark.value).toBe(true)
  })

  it('returns current theme value', () => {
    const { currentTheme, setTheme } = useTheme()

    setTheme('dark')
    expect(currentTheme()).toBe('dark')

    setTheme('light')
    expect(currentTheme()).toBe('light')
  })

  it('persists theme to localStorage', async () => {
    const { setTheme } = useTheme()

    setTheme('dark')

    // Wait for Vue to update
    await new Promise(resolve => setTimeout(resolve, 10))

    const stored = localStorage.getItem('portfolio-theme')
    expect(stored).toBeTruthy()
  })

  it('applies theme attribute to HTML element', async () => {
    const { setTheme } = useTheme()

    setTheme('dark')

    // Wait for Vue to update DOM
    await new Promise(resolve => setTimeout(resolve, 10))

    const htmlTheme = document.documentElement.getAttribute('data-theme')
    expect(htmlTheme).toBe('dark')
  })

  it('dispatches theme-changed event', async () => {
    const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent')

    const { toggleTheme } = useTheme()
    toggleTheme()

    // Wait for watch effect to trigger
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(dispatchEventSpy).toHaveBeenCalled()

    dispatchEventSpy.mockRestore()
  })

  it('respects system preference when no stored theme', () => {
    // Mock system prefers dark mode
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)',
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn()
    }))

    const { isDark } = useTheme()

    // Should detect system preference
    expect(isDark.value).toBe(true)
  })
})
