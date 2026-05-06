import { computed, type Ref, type WritableComputedRef } from 'vue'

/**
 * Two-way binding adapter between a `string[]` form field and a single
 * comma-separated `<input>`. Used by the admin views for technologies
 * and responsibilities lists; previously triplicated as inline
 * computeds and slowly drifting apart.
 *
 * Whitespace is trimmed and empty entries are dropped on parse.
 */
export function useCommaSeparatedList<T extends Record<string, unknown>>(
  form: Ref<T>,
  key: keyof T
): WritableComputedRef<string> {
  return computed<string>({
    get(): string {
      const value = form.value[key]
      return Array.isArray(value) ? (value as string[]).join(', ') : ''
    },
    set(input: string): void {
      const parsed = input
        .split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0)
      // Cast through unknown — the caller declared this key as string[].
      ;(form.value[key] as unknown) = parsed
    }
  })
}
