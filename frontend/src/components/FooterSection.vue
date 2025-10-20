<template>
  <footer class="footer-section">
    <div class="container">
      <div class="footer-content">
        <p>&copy; {{ currentYear }} David Dashti. All rights reserved.</p>
      </div>
    </div>

    <!-- Scroll to Top Button -->
    <button v-if="showScrollTop" @click="scrollToTop" class="scroll-to-top" aria-label="Scroll to top">
      <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2l-12 12h7v8h10v-8h7z"/>
      </svg>
    </button>
  </footer>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const showScrollTop = ref(false)
const currentYear = computed(() => new Date().getFullYear())

const scrollToSection = (sectionId) => {
  const element = document.getElementById(sectionId)
  if (element) {
    const navHeight = 70
    const elementPosition = element.getBoundingClientRect().top + window.pageYOffset
    const offsetPosition = elementPosition - navHeight

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    })
  }
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

const handleScroll = () => {
  showScrollTop.value = window.scrollY > 300
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.footer-section {
  background: var(--bg-tertiary, #dbeafe);
  color: var(--text-secondary, #475569);
  padding: 2rem 0;
  text-align: center;
  border-top: 1px solid var(--border-primary, #bfdbfe);
}

.footer-content {
  margin: 0;
}

.footer-content p {
  margin: 0;
  font-size: 0.9rem;
}

/* Scroll to Top Button */
.scroll-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--primary-600, #2563eb);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
}

.scroll-to-top:hover {
  background: var(--primary-700, #1d4ed8);
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.scroll-to-top svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 768px) {
  .footer-section {
    padding: 1.5rem 0;
  }

  .scroll-to-top {
    bottom: 1rem;
    right: 1rem;
    width: 40px;
    height: 40px;
  }
}
</style>