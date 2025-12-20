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
        <img
          :src="logoSrc"
          alt="David Dashti Logo"
          height="30"
          class="d-inline-block align-text-top me-2"
          loading="lazy"
        />
        David Dashti
      </a>
      <!-- Theme toggle always visible on mobile -->
      <div class="d-flex align-items-center order-lg-2 theme-toggle-container">
        <ThemeToggle />
        <button
          class="navbar-toggler ms-2 d-lg-none"
          type="button"
          data-testid="mobile-menu-toggle"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation menu"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>
      <div id="navbarNav" class="collapse navbar-collapse order-lg-1">
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ThemeToggle from './ThemeToggle.vue'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()

// Compute logo path based on theme
const logoSrc = computed(() => (isDark.value ? '/images/D-white.svg' : '/images/D-dark.svg'))

interface NavItem {
  name: string
  href: string
}

const scrolled = ref<boolean>(false)
const activeSection = ref<string>('hero')

const navItems: NavItem[] = [
  { name: 'Home', href: 'hero' },
  { name: 'Experience', href: 'experience' },
  { name: 'Education', href: 'education' },
  { name: 'Projects', href: 'projects' },
  { name: 'About', href: 'about' }
]

// Smooth scroll to section
const scrollToSection = (sectionId: string): void => {
  const element = document.getElementById(sectionId)
  if (element) {
    const navHeight = 70 // Account for fixed navbar
    const elementPosition = element.getBoundingClientRect().top + window.pageYOffset
    const offsetPosition = elementPosition - navHeight

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    })

    // Update active section
    activeSection.value = sectionId

    // Close mobile menu if open
    const navbarCollapse = document.querySelector('.navbar-collapse')
    if (navbarCollapse && navbarCollapse.classList.contains('show')) {
      navbarCollapse.classList.remove('show')
    }
  }
}

// Handle scroll events
const handleScroll = (): void => {
  // Update navbar background on scroll
  scrolled.value = window.scrollY > 50

  // Update active section based on scroll position
  const sections: string[] = ['hero', 'experience', 'education', 'projects', 'about']
  const scrollPosition = window.scrollY + 100

  for (const sectionId of sections) {
    const element = document.getElementById(sectionId)
    if (element) {
      const { offsetTop, offsetHeight } = element
      if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
        activeSection.value = sectionId
        break
      }
    }
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  handleScroll() // Initial check
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.navbar-custom {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding: 0.75rem 0;
}

.navbar-scrolled {
  padding: 0.5rem 0;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--slate-800, #1e293b);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  transition: all 0.2s ease;
}

.navbar-brand:hover {
  color: var(--primary-600, #2563eb);
}

.navbar-brand img {
  transition: transform 0.2s ease;
}

.navbar-brand:hover img {
  transform: scale(1.05);
}

.nav-link {
  color: var(--slate-600, #475569) !important;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0.5rem 1rem !important;
  margin: 0 0.125rem !important;
  text-decoration: none;
  transition: all 0.2s ease;
  border-radius: 6px;
  position: relative;
}

.nav-link:hover {
  color: var(--primary-600, #2563eb) !important;
  background: var(--color-primary-alpha-10, rgba(37, 99, 235, 0.1)) !important;
}

.nav-link:focus-visible {
  outline: 2px solid var(--primary-500, #3b82f6);
  outline-offset: 2px;
  border-radius: 4px;
}

.nav-link.active {
  color: var(--primary-600, #2563eb) !important;
  background: rgba(37, 99, 235, 0.1) !important;
  font-weight: 600;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: var(--primary-600, #2563eb);
  border-radius: 1px;
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

[data-theme='dark'] .nav-link:hover {
  color: var(--link-color) !important;
  background: var(--color-hover-bg) !important;
}

[data-theme='dark'] .nav-link.active {
  color: var(--link-color) !important;
  background: var(--color-primary-alpha-20) !important;
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

  .nav-link.active::after {
    display: none;
  }

  .nav-link.active {
    background: var(--primary-600) !important;
    color: var(--text-inverse) !important;
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
