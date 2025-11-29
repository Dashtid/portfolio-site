<template>
  <footer class="footer-section">
    <div class="container">
      <div class="footer-content">
        <!-- Brand and tagline -->
        <div class="footer-brand">
          <img src="/images/D-dark.svg" alt="David Dashti Logo" class="footer-logo" loading="lazy">
          <span class="footer-name">David Dashti</span>
        </div>
        <p class="footer-tagline">Cybersecurity Engineer & Medical Software Specialist</p>

        <!-- Social Links -->
        <div class="footer-social">
          <a href="https://www.linkedin.com/in/david-dashti/" target="_blank" rel="noopener noreferrer" class="social-link" aria-label="LinkedIn Profile">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
            </svg>
          </a>
          <a href="https://github.com/Dashtid" target="_blank" rel="noopener noreferrer" class="social-link" aria-label="GitHub Profile">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
        </div>

        <!-- Divider -->
        <div class="footer-divider"></div>

        <!-- Copyright -->
        <p class="footer-copyright">&copy; {{ currentYear }} David Dashti. All rights reserved.</p>
      </div>
    </div>

    <!-- Scroll to Top Button -->
    <Transition name="fade">
      <button v-if="showScrollTop" @click="scrollToTop" class="scroll-to-top" aria-label="Scroll to top">
        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7"/>
        </svg>
      </button>
    </Transition>
  </footer>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const showScrollTop = ref(false)
const currentYear = computed(() => new Date().getFullYear())

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
  background: linear-gradient(180deg, var(--bg-primary, #ffffff) 0%, var(--bg-tertiary, #f1f5f9) 100%);
  color: var(--text-secondary, #475569);
  padding: 3rem 0 2rem;
  text-align: center;
  border-top: 1px solid var(--border-primary, #e2e8f0);
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.footer-logo {
  width: 32px;
  height: 32px;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.footer-brand:hover .footer-logo {
  opacity: 1;
}

.footer-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
}

.footer-tagline {
  font-size: 0.9rem;
  color: var(--text-tertiary, #64748b);
  margin: 0;
}

.footer-social {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--bg-secondary, #f8fafc);
  color: var(--text-secondary, #475569);
  border: 1px solid var(--border-primary, #e2e8f0);
  transition: all 0.2s ease;
}

.social-link:hover {
  background: var(--primary-600, #2563eb);
  color: white;
  border-color: var(--primary-600, #2563eb);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.footer-divider {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--border-primary, #e2e8f0), transparent);
  margin: 0.5rem 0;
}

.footer-copyright {
  font-size: 0.85rem;
  color: var(--text-tertiary, #64748b);
  margin: 0;
}

/* Scroll to Top Button */
.scroll-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--primary-600, #2563eb);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
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
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
}

.scroll-to-top svg {
  width: 20px;
  height: 20px;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Dark theme */
[data-theme="dark"] .footer-section {
  background: linear-gradient(180deg, var(--bg-primary, #0f172a) 0%, #0c1222 100%);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

[data-theme="dark"] .footer-name {
  color: #f1f5f9;
}

[data-theme="dark"] .footer-tagline,
[data-theme="dark"] .footer-copyright {
  color: #94a3b8;
}

[data-theme="dark"] .social-link {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

[data-theme="dark"] .social-link:hover {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

[data-theme="dark"] .footer-divider {
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
}

[data-theme="dark"] .footer-logo {
  filter: invert(1) brightness(0.9);
}

/* Mobile styles */
@media (max-width: 768px) {
  .footer-section {
    padding: 2rem 0 1.5rem;
  }

  .footer-name {
    font-size: 1.1rem;
  }

  .footer-tagline {
    font-size: 0.85rem;
  }

  .scroll-to-top {
    bottom: 1.5rem;
    right: 1.5rem;
    width: 44px;
    height: 44px;
  }
}
</style>
