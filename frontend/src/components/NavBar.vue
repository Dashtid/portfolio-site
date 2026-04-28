<template>
  <nav
    class="navbar navbar-expand-lg navbar-light fixed-top navbar-custom"
    :class="{ 'navbar-scrolled': scrolled }"
    data-testid="navbar"
    role="navigation"
    aria-label="Main navigation"
  >
    <div class="container">
      <a
        aria-label="David Dashti - Home"
        class="navbar-brand"
        href="#hero"
        @click="scrollToSection('hero')"
      >
        David Dashti
      </a>
      <!-- Theme toggle always visible on mobile -->
      <div class="d-flex align-items-center order-lg-2 theme-toggle-container">
        <ThemeToggle />
        <button
          class="navbar-toggler ms-2 d-lg-none"
          type="button"
          data-testid="mobile-menu-toggle"
          aria-controls="navbarNav"
          :aria-expanded="mobileMenuOpen"
          aria-label="Toggle navigation menu"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>
      <div
        id="navbarNav"
        class="collapse navbar-collapse order-lg-1"
        :class="{ show: mobileMenuOpen }"
      >
        <ul class="navbar-nav ms-auto">
          <li v-for="item in navItems" :key="item.href" class="nav-item">
            <a
              class="nav-link"
              :class="{ active: activeSection === item.href }"
              :href="`#${item.href}`"
              :data-testid="`nav-link-${item.href}`"
              :aria-label="`Navigate to ${item.name} section`"
              :aria-current="activeSection === item.href ? 'page' : undefined"
              @click.prevent="scrollToSection(item.href)"
            >
              {{ item.name }}
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ThemeToggle from './ThemeToggle.vue'

const route = useRoute()
const router = useRouter()

// On the home route we track which section is in view via scroll; on other
// routes we highlight a static section based on the URL (e.g. /experience/:id
// → highlight 'experience'). isHomeRoute gates scroll-vs-navigate behavior.
const isHomeRoute = computed(() => route.path === '/')
const routeSection = computed(() => {
  if (route.path.startsWith('/experience/') || route.path.startsWith('/company/')) {
    return 'experience'
  }
  return ''
})

interface NavItem {
  name: string
  href: string
}

const scrolled = ref<boolean>(false)
const activeSection = ref<string>('hero')
const mobileMenuOpen = ref<boolean>(false)

const navItems: NavItem[] = [
  { name: 'Home', href: 'hero' },
  { name: 'Experience', href: 'experience' },
  { name: 'Education', href: 'education' },
  { name: 'Projects', href: 'projects' },
  { name: 'About', href: 'about' }
]

// Cache for section elements (avoids repeated DOM queries)
const sectionElementsCache = ref<Map<string, HTMLElement>>(new Map())

// Initialize section element cache
const initSectionCache = (): void => {
  const sectionIds = ['hero', 'experience', 'education', 'projects', 'about']
  sectionIds.forEach(id => {
    const element = document.getElementById(id)
    if (element) {
      sectionElementsCache.value.set(id, element)
    } else if (import.meta.env.DEV) {
      // Warn in development if expected sections are missing
      console.warn(`[NavBar] Navigation section "${id}" not found in DOM`)
    }
  })
}

// Simple throttle function (avoids adding lodash dependency)
const throttle = (func: () => void, limit: number): (() => void) => {
  let inThrottle = false
  return () => {
    if (!inThrottle) {
      func()
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

// Navigate to a section. On the home route, smooth-scroll in place; on other
// routes, route to /#section — the router's scrollBehavior handles the scroll.
const scrollToSection = (sectionId: string): void => {
  if (!isHomeRoute.value) {
    mobileMenuOpen.value = false
    router.push({ path: '/', hash: `#${sectionId}` })
    return
  }

  let element = sectionElementsCache.value.get(sectionId)
  if (!element) {
    // Cache miss - query DOM and store result for future use
    element = document.getElementById(sectionId) ?? undefined
    if (element) {
      sectionElementsCache.value.set(sectionId, element)
    }
  }
  if (element) {
    // Use the navbar's actual rendered height so the section's top edge
    // lands exactly at the navbar's bottom — no bleed of the previous
    // section above. Navbar height changes between default and scrolled
    // states, so reading it live keeps the math correct in both.
    const navbar = document.querySelector('.navbar-custom')
    const navHeight = navbar?.getBoundingClientRect().height ?? 72
    const elementPosition = element.getBoundingClientRect().top + window.pageYOffset
    const offsetPosition = elementPosition - navHeight

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    })

    // Update active section
    activeSection.value = sectionId

    // Close mobile menu if open
    mobileMenuOpen.value = false

    // Set focus to target section for accessibility (screen readers)
    // Temporarily set tabindex="-1" to make non-interactive elements focusable
    const hadTabindex = element.hasAttribute('tabindex')
    if (!hadTabindex) {
      element.setAttribute('tabindex', '-1')
    }
    element.focus({ preventScroll: true })
    // Remove the temporary tabindex to avoid polluting the DOM
    if (!hadTabindex) {
      element.removeAttribute('tabindex')
    }
  }
}

// Handle scroll events (uses cached elements for performance)
const handleScroll = (): void => {
  // Update navbar background on scroll
  scrolled.value = window.scrollY > 50

  // Active-section tracking only applies on the home route (sections don't
  // exist on other pages).
  if (!isHomeRoute.value) return

  const scrollPosition = window.scrollY + 100
  const sectionIds = ['hero', 'experience', 'education', 'projects', 'about']

  for (const sectionId of sectionIds) {
    const element = sectionElementsCache.value.get(sectionId)
    if (element) {
      const { offsetTop, offsetHeight } = element
      // Validate values are finite numbers to prevent comparison issues
      if (
        Number.isFinite(offsetTop) &&
        Number.isFinite(offsetHeight) &&
        scrollPosition >= offsetTop &&
        scrollPosition < offsetTop + offsetHeight
      ) {
        activeSection.value = sectionId
        break
      }
    }
  }
}

// Throttled scroll handler (100ms delay reduces CPU usage significantly)
const throttledHandleScroll = throttle(handleScroll, 100)

// Keeps the --navbar-height CSS variable in sync with the actual rendered
// navbar height (it shrinks ~16px when scrolled). Used by scroll-padding-top
// for hash anchors and by the router's scrollBehavior.
let navbarResizeObserver: ResizeObserver | null = null

const syncNavbarHeight = (height: number): void => {
  document.documentElement.style.setProperty('--navbar-height', `${Math.round(height)}px`)
}

onMounted(() => {
  // Initialize element cache after DOM is ready
  initSectionCache()
  // Use throttled handler for scroll events
  window.addEventListener('scroll', throttledHandleScroll, { passive: true })
  handleScroll() // Initial check

  const navbar = document.querySelector('.navbar-custom')
  if (navbar) {
    syncNavbarHeight(navbar.getBoundingClientRect().height)
    if (typeof ResizeObserver !== 'undefined') {
      navbarResizeObserver = new ResizeObserver(entries => {
        syncNavbarHeight(entries[0].contentRect.height)
      })
      navbarResizeObserver.observe(navbar)
    }
  }
})

// When navigating to a non-home route, reflect that in the active-link
// highlight so (e.g.) 'Experience' stays highlighted on /experience/:id.
watch(
  routeSection,
  section => {
    if (section) activeSection.value = section
  },
  { immediate: true }
)

onUnmounted(() => {
  window.removeEventListener('scroll', throttledHandleScroll)
  sectionElementsCache.value.clear()
  navbarResizeObserver?.disconnect()
  navbarResizeObserver = null
})
</script>

<style scoped>
.navbar-custom {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: all 0.3s var(--ease-smooth, cubic-bezier(0.4, 0, 0.2, 1));
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding: 1rem 0;
}

.navbar-scrolled {
  padding: 0.5rem 0;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
}

.navbar-brand {
  font-family: var(--font-family-display, inherit);
  font-weight: 600;
  font-size: 1.25rem;
  letter-spacing: var(--letter-spacing-tight, -0.025em);
  color: var(--text-primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  transition:
    color 0.2s var(--ease-smooth, ease),
    transform 0.2s var(--ease-smooth, ease);
}

.navbar-scrolled .navbar-brand {
  font-size: 1.125rem;
}

.navbar-brand:hover {
  color: var(--primary-500, #3b82f6);
}

.nav-link {
  color: var(--text-secondary) !important;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0.5rem 1rem !important;
  margin: 0 0.25rem !important;
  text-decoration: none;
  transition: color 0.2s var(--ease-smooth, ease);
  border-radius: 6px;
  position: relative;
}

/* Underline that grows from center on hover */
.nav-link::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--primary-500, #3b82f6);
  border-radius: 1px;
  transition:
    width 0.25s var(--ease-smooth, ease),
    left 0.25s var(--ease-smooth, ease);
}

.nav-link:hover {
  color: var(--primary-500, #3b82f6) !important;
}

.nav-link:hover::after {
  width: 60%;
  left: 20%;
}

.nav-link:focus-visible {
  outline: 2px solid var(--primary-500, #3b82f6);
  outline-offset: 2px;
  border-radius: 4px;
}

.nav-link.active {
  color: var(--primary-500, #3b82f6) !important;
  font-weight: 600;
}

.nav-link.active::after {
  width: 60%;
  left: 20%;
  background: var(--primary-500, #3b82f6);
}

/* Dark theme styles */
[data-theme='dark'] .navbar-custom {
  background: var(--navbar-bg);
  border-bottom: 1px solid var(--border-primary);
}

[data-theme='dark'] .navbar-scrolled {
  background: rgba(15, 23, 42, 0.98);
  box-shadow: var(--navbar-shadow);
}

[data-theme='dark'] .navbar-brand {
  color: var(--text-primary);
}

[data-theme='dark'] .navbar-brand:hover {
  color: var(--link-color);
}

[data-theme='dark'] .nav-link {
  color: var(--text-secondary) !important;
}

[data-theme='dark'] .nav-link::after {
  background: var(--link-color);
}

[data-theme='dark'] .nav-link:hover {
  color: var(--link-color) !important;
}

[data-theme='dark'] .nav-link.active {
  color: var(--link-color) !important;
}

[data-theme='dark'] .nav-link:focus-visible {
  outline-color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .nav-link.active::after {
  background: var(--link-color);
}

[data-theme='dark'] .navbar-toggler {
  border-color: var(--border-primary);
}

[data-theme='dark'] .navbar-toggler-icon {
  filter: invert(1);
}

/* Mobile styles */
@media (max-width: 991px) {
  .navbar-collapse {
    background: var(--bg-primary);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 12px;
    margin-top: 0.5rem;
    padding: 1rem;
    box-shadow: var(--shadow-lg);
  }

  .navbar-nav {
    gap: 0.25rem;
  }

  .nav-link {
    padding: 0.75rem 1rem !important;
    border-radius: 8px;
    text-align: center;
  }

  .nav-link::after {
    display: none;
  }

  .nav-link.active {
    background: var(--color-primary-alpha-15, rgba(59, 130, 246, 0.15)) !important;
    color: var(--primary-500, #3b82f6) !important;
  }

  [data-theme='dark'] .nav-link.active {
    background: var(--color-primary-alpha-20) !important;
    color: var(--link-color) !important;
  }
}

/* Theme toggle spacing on desktop */
@media (min-width: 992px) {
  .theme-toggle-container {
    margin-left: 1rem;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .nav-link,
  .navbar-custom,
  .navbar-toggler {
    transition: none;
  }
}
</style>
