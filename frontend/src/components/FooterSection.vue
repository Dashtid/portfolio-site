<template>
  <footer class="footer-section">
    <div class="container">
      <div class="row">
        <div class="col-lg-4 mb-4">
          <h4 class="footer-title">David Dashti</h4>
          <p class="footer-description">
            Security Specialist & System Developer<br>
            Bridging Healthcare Innovation with Cybersecurity Excellence
          </p>
        </div>
        <div class="col-lg-4 mb-4">
          <h5 class="footer-subtitle">Quick Links</h5>
          <ul class="footer-links">
            <li><a href="#experience" @click="scrollToSection('experience')">Experience</a></li>
            <li><a href="#education" @click="scrollToSection('education')">Education</a></li>
            <li><a href="#projects" @click="scrollToSection('projects')">Projects</a></li>
            <li><a href="#about" @click="scrollToSection('about')">About</a></li>
          </ul>
        </div>
        <div class="col-lg-4 mb-4">
          <h5 class="footer-subtitle">Connect</h5>
          <div class="social-links">
            <a href="https://github.com/Dashtid" target="_blank" rel="noopener" aria-label="GitHub">
              <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
            <a href="https://linkedin.com/in/david-dashti" target="_blank" rel="noopener" aria-label="LinkedIn">
              <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
              </svg>
            </a>
            <a href="mailto:david@dashti.se" aria-label="Email">
              <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 12.713l-11.985-9.713h23.971l-11.986 9.713zm-5.425-1.822l-6.575-5.329v12.501l6.575-7.172zm10.85 0l6.575 7.172v-12.501l-6.575 5.329zm-1.557 1.261l-3.868 3.135-3.868-3.135-8.11 8.848h23.956l-8.11-8.848z"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
      <hr class="footer-divider">
      <div class="footer-bottom">
        <p class="copyright">
          &copy; {{ currentYear }} David Dashti. All rights reserved.
        </p>
        <p class="footer-tech">
          Built with Vue.js & FastAPI | Hosted on Azure
        </p>
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
  background: var(--slate-900, #0f172a);
  color: var(--slate-300, #cbd5e1);
  padding: 4rem 0 2rem;
  position: relative;
}

.footer-title {
  color: white;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.footer-subtitle {
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.footer-description {
  line-height: 1.6;
  color: var(--slate-400, #94a3b8);
}

.footer-links {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-links li {
  margin-bottom: 0.5rem;
}

.footer-links a {
  color: var(--slate-400, #94a3b8);
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: var(--primary-400, #60a5fa);
}

.social-links {
  display: flex;
  gap: 1rem;
}

.social-links a {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--slate-800, #1e293b);
  color: var(--slate-400, #94a3b8);
  transition: all 0.3s ease;
}

.social-links a:hover {
  background: var(--primary-600, #2563eb);
  color: white;
  transform: translateY(-2px);
}

.footer-divider {
  border-color: var(--slate-700, #334155);
  margin: 3rem 0 2rem;
}

.footer-bottom {
  text-align: center;
}

.copyright {
  margin-bottom: 0.5rem;
  color: var(--slate-400, #94a3b8);
}

.footer-tech {
  font-size: 0.9rem;
  color: var(--slate-500, #64748b);
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

/* Dark theme adjustments */
[data-theme="dark"] .footer-section {
  background: #0a0a0a;
}

[data-theme="dark"] .social-links a {
  background: var(--slate-700, #334155);
}

@media (max-width: 768px) {
  .footer-section {
    padding: 3rem 0 1.5rem;
  }

  .footer-bottom {
    font-size: 0.9rem;
  }

  .scroll-to-top {
    bottom: 1rem;
    right: 1rem;
    width: 40px;
    height: 40px;
  }
}
</style>