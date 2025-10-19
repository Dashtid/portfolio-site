<template>
  <div class="portfolio-home">
    <!-- Hero Section -->
    <header class="hero">
      <div class="hero-content">
        <h1 class="hero-title">David Dashti</h1>
        <p class="hero-subtitle">Full Stack Developer & DevOps Engineer</p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="container">
        <!-- Loading State -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading portfolio...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-container">
          <p class="error-message">Failed to load portfolio data</p>
          <button @click="retryLoad" class="retry-button">Try Again</button>
        </div>

        <!-- Content -->
        <div v-else>
          <!-- Experience Section -->
          <section class="experience-section">
            <h2 class="section-title">Experience</h2>
            <div class="experience-timeline">
              <ExperienceCard
                v-for="company in portfolioStore.companiesByDate"
                :key="company.id"
                :company="company"
              />
            </div>
          </section>

          <!-- Skills Section -->
          <section class="skills-section">
            <SkillsDisplay :skills="portfolioStore.skills" />
          </section>

          <!-- Projects Section -->
          <section class="projects-section">
            <h2 class="section-title">Featured Projects</h2>
            <div class="projects-grid">
              <ProjectCard
                v-for="project in portfolioStore.projects"
                :key="project.id"
                :project="project"
              />
            </div>
          </section>

          <!-- Contact Section -->
          <section class="contact-section">
            <h2 class="section-title">Get In Touch</h2>
            <div class="contact-content">
              <p class="contact-text">
                I'm always interested in hearing about new opportunities and exciting projects.
              </p>
              <div class="contact-links">
                <a href="https://github.com/daviddashti" target="_blank" rel="noopener" class="contact-link">
                  GitHub
                </a>
                <a href="https://linkedin.com/in/daviddashti" target="_blank" rel="noopener" class="contact-link">
                  LinkedIn
                </a>
                <a href="mailto:david@dashti.se" class="contact-link">
                  Email
                </a>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import ExperienceCard from '../components/ExperienceCard.vue'
import SkillsDisplay from '../components/SkillsDisplay.vue'
import ProjectCard from '../components/ProjectCard.vue'

const portfolioStore = usePortfolioStore()
const loading = ref(true)
const error = ref(null)

const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    await portfolioStore.fetchAllData()
  } catch (err) {
    error.value = err.message
    console.error('Error loading portfolio:', err)
  } finally {
    loading.value = false
  }
}

const retryLoad = () => {
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.portfolio-home {
  min-height: 100vh;
  background: var(--color-gray-50);
}

/* Hero Section */
.hero {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-teal) 100%);
  color: white;
  padding: var(--spacing-24) 0;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: var(--font-size-5xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-normal);
  margin-top: var(--spacing-2);
  opacity: 0.95;
}

/* Main Content */
.main-content {
  padding: var(--spacing-16) 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}

/* Section Styles */
.section-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-8);
  text-align: center;
}

.experience-section,
.skills-section,
.projects-section,
.contact-section {
  margin-bottom: var(--spacing-16);
}

.experience-timeline {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-6);
}

/* Contact Section */
.contact-section {
  text-align: center;
}

.contact-content {
  max-width: 600px;
  margin: 0 auto;
}

.contact-text {
  font-size: var(--font-size-lg);
  color: var(--color-gray-600);
  margin-bottom: var(--spacing-6);
  line-height: var(--line-height-relaxed);
}

.contact-links {
  display: flex;
  justify-content: center;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.contact-link {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-6);
  background: white;
  color: var(--color-gray-700);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
  border: 2px solid var(--color-gray-200);
  transition: all var(--transition-base) ease;
}

.contact-link:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Loading State */
.loading-container {
  text-align: center;
  padding: var(--spacing-16) 0;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  margin: 0 auto var(--spacing-4);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-container {
  text-align: center;
  padding: var(--spacing-16) 0;
}

.error-message {
  color: var(--color-red);
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-4);
}

.retry-button {
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.retry-button:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero-title {
    font-size: var(--font-size-3xl);
  }

  .hero-subtitle {
    font-size: var(--font-size-lg);
  }

  .section-title {
    font-size: var(--font-size-2xl);
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>