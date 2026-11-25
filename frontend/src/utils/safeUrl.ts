/**
 * Scheme guard for URLs from the API or the admin CMS that are bound to an
 * href or src. Vue sets bound attributes verbatim, so a stored javascript: or
 * data: URL would otherwise reach the DOM as a working link.
 */
const ALLOWED_PROTOCOLS = new Set(['https:', 'http:', 'mailto:'])

/**
 * Returns the value unchanged when the WHATWG URL parser, which browsers use
 * for href and src, gives it an https, http or mailto scheme. A relative
 * reference takes the page's scheme. Anything else returns undefined, and
 * Vue then leaves the attribute out.
 */
export const safeUrl = (value: string | null | undefined): string | undefined => {
  if (value == null) return undefined
  try {
    return ALLOWED_PROTOCOLS.has(new URL(value, 'https://dashti.se').protocol) ? value : undefined
  } catch {
    return undefined
  }
}
