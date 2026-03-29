import { computed, type Ref } from 'vue'

/**
 * Validates an embed URL against an allowlist of hosts and a required path prefix.
 * Returns a computed ref that resolves to the URL if valid, or null if blocked.
 *
 * Guards:
 * - Protocol must be https
 * - Hostname must be in allowedHosts
 * - Pathname must start with requiredPathPrefix
 *
 * DEV-only console warnings identify which check failed without leaking info in production.
 */
export function useEmbedValidator(
  url: Ref<string>,
  allowedHosts: string[],
  requiredPathPrefix: string,
  debugLabel: string
) {
  return computed<string | null>(() => {
    if (!url.value) return null

    try {
      const parsed = new URL(url.value)

      if (parsed.protocol !== 'https:') {
        if (import.meta.env.DEV) {
          console.warn(`[${debugLabel}] Blocked non-https URL: ${url.value}`)
        }
        return null
      }

      if (!allowedHosts.includes(parsed.hostname)) {
        if (import.meta.env.DEV) {
          console.warn(`[${debugLabel}] Blocked disallowed host: ${url.value}`)
        }
        return null
      }

      if (!parsed.pathname.startsWith(requiredPathPrefix)) {
        if (import.meta.env.DEV) {
          console.warn(`[${debugLabel}] Blocked non-embed path: ${url.value}`)
        }
        return null
      }

      return url.value
    } catch {
      if (import.meta.env.DEV) {
        console.warn(`[${debugLabel}] Invalid URL: ${url.value}`)
      }
      return null
    }
  })
}
