<template>
  <nav
    class="navbar navbar-expand-lg navbar-light fixed-top navbar-custom"
    :class="{ 'navbar-scrolled': scrolled }"
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
          src="/images/D-dark.svg"
          alt="David Dashti Logo"
          height="30"
          class="d-inline-block align-text-top me-2"
          loading="lazy"
        />
        David Dashti
      </a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation menu"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div id="navbarNav" class="collapse navbar-collapse">
        <ul class="navbar-nav ms-auto">
          <li v-for="item in navItems" :key="item.href" class="nav-item">
            <a
              class="nav-link"
              :class="{ active: activeSection === item.href }"
              :href="`#${item.href}`"
              :aria-label="`Navigate to ${item.name} section`"
              :aria-current="activeSection === item.href ? 'page' : undefined"
              @click.prevent="scrollToSection(item.href)"
            >
              {{ item.name }}
            </a>
          </li>
          <li class="nav-item ms-2">
            <ThemeToggle />
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ThemeToggle from './ThemeToggle.vue'

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
  { name: 'About', href: 'about' },
  { name: 'Contact', href: 'contact' }
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
  const sections: string[] = ['hero', 'experience', 'education', 'projects', 'about', 'contact']
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
  background: rgba(37, 99, 235, 0.08) !important;
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
  background: rgba(15, 23, 42, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

[data-theme='dark'] .navbar-scrolled {
  background: rgba(15, 23, 42, 0.98);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .navbar-brand {
  color: #f1f5f9;
}

[data-theme='dark'] .navbar-brand:hover {
  color: #60a5fa;
}

[data-theme='dark'] .nav-link {
  color: #94a3b8 !important;
}

[data-theme='dark'] .nav-link:hover {
  color: #60a5fa !important;
  background: rgba(96, 165, 250, 0.1) !important;
}

[data-theme='dark'] .nav-link.active {
  color: #60a5fa !important;
  background: rgba(96, 165, 250, 0.15) !important;
}

[data-theme='dark'] .nav-link.active::after {
  background: #60a5fa;
}

[data-theme='dark'] .navbar-toggler {
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .navbar-toggler-icon {
  filter: invert(1);
}

/* Mobile styles */
@media (max-width: 991px) {
  .navbar-collapse {
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 12px;
    margin-top: 0.5rem;
    padding: 1rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  }

  [data-theme='dark'] .navbar-collapse {
    background: rgba(30, 41, 59, 0.98);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
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
    background: var(--primary-600, #2563eb) !important;
    color: white !important;
  }

  [data-theme='dark'] .nav-link.active {
    background: #3b82f6 !important;
    color: white !important;
  }
}
</style>
