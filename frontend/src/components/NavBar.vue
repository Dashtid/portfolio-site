<template>
  <nav class="navbar navbar-expand-lg navbar-light fixed-top navbar-custom" :class="{ 'navbar-scrolled': scrolled }" role="navigation" aria-label="Main navigation">
    <div class="container">
      <a class="navbar-brand" href="#hero" @click="scrollToSection('hero')" aria-label="David Dashti - Home">
        <img src="/images/D-dark.svg" alt="David Dashti Logo" height="30" class="d-inline-block align-text-top me-2" loading="lazy">
        David Dashti
      </a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation menu">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item" v-for="item in navItems" :key="item.href">
            <a class="nav-link" :class="{ active: activeSection === item.href }"
               :href="`#${item.href}`"
               :aria-label="`Navigate to ${item.name} section`"
               :aria-current="activeSection === item.href ? 'page' : undefined"
               @click.prevent="scrollToSection(item.href)">
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

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ThemeToggle from './ThemeToggle.vue'

const scrolled = ref(false)
const activeSection = ref('hero')

const navItems = [
  { name: 'Home', href: 'hero' },
  { name: 'Experience', href: 'experience' },
  { name: 'Education', href: 'education' },
  { name: 'Projects', href: 'projects' },
  { name: 'About', href: 'about' },
  { name: 'Contact', href: 'contact' }
]

// Smooth scroll to section
const scrollToSection = (sectionId) => {
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
const handleScroll = () => {
  // Update navbar background on scroll
  scrolled.value = window.scrollY > 50

  // Update active section based on scroll position
  const sections = ['hero', 'experience', 'education', 'projects', 'about', 'contact']
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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 1rem 0;
}

.navbar-scrolled {
  padding: 0.5rem 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--primary-600, #2563eb);
  text-decoration: none;
  display: flex;
  align-items: center;
  background: var(--bg-secondary, #fff);
  border: 1px solid var(--border-secondary, #93c5fd);
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.navbar-brand:hover {
  color: var(--primary-700, #1d4ed8);
  background: var(--bg-accent, #dbeafe);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.nav-link {
  color: var(--slate-700, #334155) !important;
  font-weight: 500;
  background: var(--bg-secondary, #fff) !important;
  border: 1px solid var(--border-secondary, #93c5fd) !important;
  border-radius: 0.5rem !important;
  padding: 0.5rem 1rem !important;
  margin: 0 0.25rem !important;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.nav-link:hover {
  background: var(--bg-accent, #dbeafe) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.nav-link.active {
  background: var(--primary-600, #2563eb) !important;
  color: white !important;
  border-color: var(--primary-600, #2563eb) !important;
  box-shadow: 0 10px 15px rgba(37, 99, 235, 0.2);
}


/* Dark theme styles */
[data-theme="dark"] .navbar-custom {
  background: rgba(30, 41, 59, 0.95);
}

[data-theme="dark"] .navbar-brand {
  color: #60a5fa;
}

[data-theme="dark"] .nav-link {
  color: #cbd5e1;
}

[data-theme="dark"] .nav-link:hover,
[data-theme="dark"] .nav-link.active {
  color: #60a5fa;
}

@media (max-width: 768px) {
  .navbar-nav {
    text-align: center;
    padding: 1rem 0;
  }

  .nav-link {
    padding: 0.5rem 0;
  }

  .nav-link.active::after {
    display: none;
  }
}
</style>