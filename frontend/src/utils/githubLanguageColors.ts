/**
 * GitHub language palette used by the language dot on repo cards.
 *
 * Source: GitHub Linguist's published colors-by-language list. Only the
 * languages that actually appear in this site's GitHub data are listed
 * here; unknown languages fall back to `--primary-600` blue so the dot
 * still renders.
 */

export const githubLanguageColors: Record<string, string> = {
  TypeScript: '#3178c6',
  JavaScript: '#f1e05a',
  Python: '#3572A5',
  Vue: '#41b883',
  HTML: '#e34c26',
  CSS: '#563d7c',
  SCSS: '#c6538c',
  Shell: '#89e051',
  Go: '#00ADD8',
  Rust: '#dea584',
  Java: '#b07219',
  'C++': '#f34b7d',
  C: '#555555',
  'C#': '#239120',
  Ruby: '#701516',
  PHP: '#4F5D95',
  Swift: '#F05138',
  Kotlin: '#A97BFF',
  Dart: '#00B4AB'
}

const FALLBACK_COLOR = '#3b82f6'

export const getLanguageColor = (lang: string | null | undefined): string => {
  if (!lang) return FALLBACK_COLOR
  return githubLanguageColors[lang] ?? FALLBACK_COLOR
}
