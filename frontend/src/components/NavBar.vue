<template>
  <nav
    class="navbar-custom fixed inset-x-0 top-0 z-50 transition-all duration-300"
    :class="scrolled ? 'navbar-scrolled' : ''"
    data-testid="navbar"
    role="navigation"
    aria-label="Main navigation"
  >
    <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6">
      <a
        aria-label="David Dashti - Home"
        class="navbar-brand"
        href="#hero"
        @click.prevent="scrollToSection('hero')"
      >
        David Dashti
      </a>

      <!-- Desktop nav -->
      <ul class="ml-auto hidden items-center gap-1 lg:flex">
        <li v-for="item in navItems" :key="item.href">
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

      <!-- Right cluster: theme toggle + mobile menu button -->
      <div class="flex items-center gap-2">
        <ThemeToggle />
        <button
          class="navbar-toggler inline-flex h-10 w-10 items-center justify-center rounded-lg text-slate-700 transition-colors hover:bg-slate-100 lg:hidden dark:text-slate-300 dark:hover:bg-slate-800"
          type="button"
          data-testid="mobile-menu-toggle"
          aria-controls="navbarNav"
          :aria-expanded="mobileMenuOpen"
          aria-label="Toggle navigation menu"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <svg
            class="h-5 w-5"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              :d="mobileMenuOpen ? 'M6 18 18 6M6 6l12 12' : 'M4 7h16M4 12h16M4 17h16'"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile menu. Uses .navbar-collapse + .show classes to keep test
         selectors stable and so the existing data-anim/transition CSS
         continues to apply. v-show keeps the DOM mounted so the scroll
         logic can hide the menu after a link click. -->
    <div
      id="navbarNav"
      class="navbar-collapse mx-6 mt-2 overflow-hidden border-t border-slate-200 transition-[max-height] duration-300 ease-out lg:hidden dark:border-slate-800"
      :class="mobileMenuOpen ? 'show max-h-96' : 'max-h-0 border-transparent'"
    >
      <ul class="flex flex-col gap-1 py-2">
        <li v-for="item in navItems" :key="item.href">
          <a
            class="nav-link block w-full rounded-lg px-4 py-2.5 text-center"
            :class="{ active: activeSection === item.href }"
            :href="`#${item.href}`"
            :data-testid="`nav-link-${item.href}-mobile`"
            :aria-label="`Navigate to ${item.name} section`"
            @click.prevent="scrollToSection(item.href)"
          >
            {{ item.name }}
          </a>
        </li>
      </ul>
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
    // Use the scrolled-state navbar height (cached in --navbar-height by
    // syncNavbarHeight). At any non-hero target the navbar will be in
    // scrolled state at scroll-end, so this matches the final layout
    // exactly. Reading the live (currently-default) height instead would
    // overshoot when scrolling away from the top.
    const navHeightStr = getComputedStyle(document.documentElement).getPropertyValue(
      '--navbar-height'
    )
    const navHeight = parseInt(navHeightStr, 10) || 56
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

// Measures the navbar's scrolled-state height — this is what the navbar
// will be at *any* non-hero scroll target (since scrolling > 50px puts
// it in scrolled state). Using it as the offset everywhere avoids the
// home→experience gap where the navbar is currently tall (default) but
// will shrink mid-scroll, leaving a visible bleed of the previous
// section above the target. Transitions are temporarily disabled so the
// measurement reflects the final layout, not an in-flight intermediate.
const measureScrolledNavHeight = (): number => {
  const navbar = document.querySelector<HTMLElement>('.navbar-custom')
  if (!navbar) return 56
  const origTransition = navbar.style.transition
  navbar.style.transition = 'none'
  const wasScrolled = navbar.classList.contains('navbar-scrolled')
  navbar.classList.add('navbar-scrolled')
  void navbar.offsetHeight
  const h = navbar.getBoundingClientRect().height
  if (!wasScrolled) navbar.classList.remove('navbar-scrolled')
  void navbar.offsetHeight
  navbar.style.transition = origTransition
  return h
}

const syncNavbarHeight = (): void => {
  const h = measureScrolledNavHeight()
  document.documentElement.style.setProperty('--navbar-height', `${Math.round(h)}px`)
}

onMounted(() => {
  // Initialize element cache after DOM is ready
  initSectionCache()
  // Use throttled handler for scroll events
  window.addEventListener('scroll', throttledHandleScroll, { passive: true })
  handleScroll() // Initial check

  syncNavbarHeight()
  // Re-measure on viewport resize (mobile/desktop breakpoints can change
  // navbar dimensions). Scroll-state changes don't affect the value we
  // store — that's the point.
  window.addEventListener('resize', syncNavbarHeight)
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
  window.removeEventListener('resize', syncNavbarHeight)
  sectionElementsCache.value.clear()
})
</script>

<style scoped>
/* Layout + chrome. Tailwind utilities in the template handle spacing and
   the dark hover states; this scoped block owns the bits that are easier
   to express in CSS (glassmorphism backdrop, the center-growing nav
   underline, the active-state colors). */

.navbar-custom {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid transparent;
  padding-block: 1rem;
}

.navbar-scrolled {
  background: rgba(255, 255, 255, 0.96);
  border-bottom-color: rgba(15, 23, 42, 0.06);
  padding-block: 0.5rem;
}

.navbar-brand {
  font-family: var(--font-family-display, inherit);
  font-weight: 600;
  font-size: 1.125rem;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.navbar-brand:hover {
  color: var(--primary-500, #3b82f6);
}

.nav-link {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.875rem;
  padding: 0.5rem 0.875rem;
  text-decoration: none;
  border-radius: 6px;
  transition: color 0.2s ease;
  position: relative;
}

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
    width 0.25s ease,
    left 0.25s ease;
}

.nav-link:hover {
  color: var(--primary-500, #3b82f6);
}

.nav-link:hover::after {
  width: 60%;
  left: 20%;
}

.nav-link:focus-visible {
  outline: 2px solid var(--primary-500, #3b82f6);
  outline-offset: 2px;
}

.nav-link.active {
  color: var(--primary-500, #3b82f6);
  font-weight: 600;
}

.nav-link.active::after {
  width: 60%;
  left: 20%;
}

/* Dark theme */
[data-theme='dark'] .navbar-custom {
  background: rgba(15, 23, 42, 0.85);
}

[data-theme='dark'] .navbar-scrolled {
  background: rgba(15, 23, 42, 0.96);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

[data-theme='dark'] .navbar-brand {
  color: var(--text-primary);
}

[data-theme='dark'] .navbar-brand:hover,
[data-theme='dark'] .nav-link:hover,
[data-theme='dark'] .nav-link.active {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .nav-link {
  color: var(--text-secondary);
}

[data-theme='dark'] .nav-link::after,
[data-theme='dark'] .nav-link.active::after {
  background: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .nav-link:focus-visible {
  outline-color: var(--primary-400, #60a5fa);
}

/* Mobile: the center-growing underline doesn't make sense on full-width
   stacked links — swap to a fill highlight instead. */
@media (max-width: 991px) {
  .nav-link::after {
    display: none;
  }

  .nav-link.active {
    background: rgba(59, 130, 246, 0.1);
  }

  [data-theme='dark'] .nav-link.active {
    background: rgba(96, 165, 250, 0.15);
  }
}

@media (prefers-reduced-motion: reduce) {
  .navbar-custom,
  .nav-link,
  .nav-link::after,
  .navbar-toggler {
    transition: none;
  }
}
</style>
