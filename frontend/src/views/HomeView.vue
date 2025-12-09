<template>
  <div class="portfolio-home">
    <!-- Navigation Bar -->
    <NavBar />

    <!-- Main content area for accessibility -->
    <main id="main-content" role="main">
      <!-- Hero Section with Stockholm Background -->
      <div class="stockholm-background">
        <section id="hero" class="hero-section">
          <div class="hero-content">
            <h1 class="custom-hero-title fade-in">
              <span class="hero-accent-primary">Cybersecurity</span> and
              <span class="hero-accent-secondary">Artificial Intelligence</span><br />
              in Medical Software Development
            </h1>
            <p class="custom-hero-lead fade-in">
              <strong>Biomedical Engineer | QA/RA & Security Specialist | Stockholm, Sweden</strong>
            </p>
          </div>
        </section>
      </div>

      <!-- Experience Section -->
      <section id="experience" class="portfolio-section">
        <div class="container">
          <h2 class="section-title">
            <img
              src="/images/experience.svg"
              alt="Experience Icon"
              class="section-icon"
              loading="lazy"
            />
            Experience
          </h2>
          <div class="experience-list">
            <!-- Dynamic content from backend or static fallback -->
            <template v-if="companies.length">
              <div
                v-for="company in companiesByDate"
                :key="company.id"
                class="experience-card fade-in"
              >
                <div class="company-header-with-logo">
                  <img
                    v-if="company.logo_url"
                    :src="company.logo_url"
                    :alt="`${company.name} Logo`"
                    class="card-logo"
                    loading="lazy"
                  />
                  <div class="company-header-content">
                    <div class="company-header">
                      <h3 class="company-name">{{ company.name }}</h3>
                      <span class="company-dates"
                        >{{ formatDate(company.start_date) }} -
                        {{ company.end_date ? formatDate(company.end_date) : 'Present' }}</span
                      >
                    </div>
                  </div>
                </div>
                <p class="job-title">{{ company.title }}</p>
                <p class="company-location">{{ company.location }}</p>
                <p class="company-description">{{ company.description }}</p>

                <!-- Learn More Button (show if company has detailed content) -->
                <router-link
                  v-if="company.detailed_description || company.video_url || company.map_url"
                  :to="{ name: 'company-detail', params: { id: company.id } }"
                  class="btn btn-outline-primary btn-sm mt-3"
                >
                  Learn More
                </router-link>
              </div>
            </template>
            <template v-else>
              <!-- Static companies as fallback -->
              <div class="experience-card fade-in">
                <div class="company-header">
                  <h3 class="company-name">Hermes Medical Solutions</h3>
                  <span class="company-dates">Sep 2022 - Present</span>
                </div>
                <p class="job-title">Security Specialist & System Developer</p>
                <p class="company-location">Stockholm, Sweden</p>
                <p class="company-description">
                  Leading cybersecurity initiatives and developing innovative healthcare solutions.
                </p>
              </div>
            </template>
          </div>
        </div>
      </section>

      <!-- Education Section -->
      <section id="education" class="portfolio-section bg-light">
        <div class="container">
          <h2 class="section-title">
            <img
              src="/images/education.svg"
              alt="Education Icon"
              class="section-icon"
              loading="lazy"
            />
            Education
          </h2>
          <div class="education-grid">
            <div v-for="edu in education" :key="edu.id" class="education-card fade-in">
              <div class="education-header-with-logo">
                <img
                  v-if="edu.logo_url"
                  :src="edu.logo_url"
                  :alt="`${edu.institution} Logo`"
                  class="card-logo"
                  loading="lazy"
                />
                <div>
                  <h3 class="education-institution">{{ edu.institution }}</h3>
                  <p class="education-degree">
                    <strong>{{ edu.degree }}</strong>
                  </p>
                </div>
              </div>
              <p class="education-field" v-if="edu.field_of_study">{{ edu.field_of_study }}</p>
              <p class="education-description" v-if="edu.description">{{ edu.description }}</p>
              <p class="education-dates">
                {{ formatDate(edu.start_date) }} -
                {{ edu.end_date ? formatDate(edu.end_date) : 'Present' }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Publications/Research Section -->
      <section id="publications" class="portfolio-section bg-dark">
        <div class="container">
          <h2 class="section-title">
            <img
              src="/images/document.svg"
              alt="Publications Icon"
              class="section-icon"
              loading="lazy"
            />
            Publications & Research
          </h2>
          <div v-if="documentsLoading" class="loading-state">Loading publications...</div>
          <div v-else-if="documentsError" class="error-state">{{ documentsError }}</div>
          <div v-else class="documents-grid">
            <DocumentCard v-for="document in documents" :key="document.id" :document="document" />
          </div>
        </div>
      </section>

      <!-- Projects Section -->
      <section id="projects" class="portfolio-section bg-light">
        <div class="container">
          <h2 class="section-title">
            <img src="/images/github.svg" alt="GitHub Icon" class="section-icon" loading="lazy" />
            GitHub
          </h2>

          <div class="projects-grid">
            <div
              v-for="project in displayProjects"
              :key="project.id || project.name"
              class="project-card fade-in"
            >
              <div class="project-content">
                <h3 class="project-title">{{ project.name }}</h3>
                <p class="project-description">{{ project.description }}</p>
                <div v-if="project.technologies" class="project-tech">
                  <span
                    v-for="tech in parseTechnologies(project.technologies)"
                    :key="tech"
                    class="tech-badge"
                  >
                    {{ tech }}
                  </span>
                </div>
                <div class="project-links">
                  <a
                    v-if="project.github_url"
                    :href="project.github_url"
                    target="_blank"
                    class="project-link"
                    >View on GitHub</a
                  >
                  <a
                    v-if="project.live_url"
                    :href="project.live_url"
                    target="_blank"
                    class="project-link"
                    >Live Demo</a
                  >
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- About Section -->
      <section id="about" class="portfolio-section">
        <div class="container">
          <h2 class="section-title">
            <img src="/images/about.svg" alt="About Icon" class="section-icon" loading="lazy" />
            About Me
          </h2>
          <div class="about-layout">
            <div class="profile-photo-container">
              <img
                src="/images/profile.png"
                alt="David Dashti - Biomedical Engineer and Cybersecurity Specialist"
                class="profile-photo"
                loading="lazy"
              />
            </div>
            <div class="about-text">
              <p>
                I am a biomedical engineer specializing in cybersecurity and regulatory compliance
                for medical software and AI systems. As a QA/RA & Security Specialist at Hermes
                Medical Solutions, I ensure that our software and digital health solutions meet the
                highest standards of security, privacy, and regulatory alignment (NIS2, ISO 27001,
                EU AI Act).
              </p>
              <p><strong>Current focus areas:</strong></p>
              <ul>
                <li>Cybersecurity governance in medical software development</li>
                <li>Ensuring compliance with NIS2 and ISO 27001</li>
                <li>Supporting market clearance for medical software (MDR, GDPR)</li>
                <li>Preparing frameworks for AI Act compliance in healthcare AI systems</li>
              </ul>
              <p>
                <strong>Technical skills:</strong> Windows Server, Unix/Linux, Docker, PowerShell
                scripting, Bash scripting, Python, Git
              </p>
              <p>
                I am passionate about making healthcare technology safer and more trustworthy by
                protecting patient data, ensuring system integrity, and helping organizations
                navigate the new AI regulatory landscape.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer Section -->
    <FooterSection />

    <!-- Back to Top Button -->
    <BackToTop />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import NavBar from '../components/NavBar.vue'
import FooterSection from '../components/FooterSection.vue'
import BackToTop from '../components/BackToTop.vue'
import DocumentCard from '../components/DocumentCard.vue'
import { useBatchAnimation } from '../composables/useScrollAnimations'
import { getDocuments } from '../api/services'
import type { Document } from '../types/api'
import { logger } from '../utils/logger'

const portfolioStore = usePortfolioStore()
const loading = ref(false)

// Computed properties for education from API
const education = computed(() => portfolioStore.education || [])

// Documents state
const documents = ref<Document[]>([])
const documentsLoading = ref(false)
const documentsError = ref<string | null>(null)

// Static projects data as fallback
const staticProjects = [
  {
    id: 'static-1',
    name: 'Portfolio Website',
    description: 'Personal portfolio showcasing professional experience and projects',
    technologies: ['Vue.js', 'Python', 'FastAPI'],
    github_url: 'https://github.com/Dashtid',
    live_url: null,
    featured: true
  }
]

// Computed properties
const companies = computed(() => portfolioStore.companies || [])
const projects = computed(() => portfolioStore.projects || [])
const companiesByDate = computed(() => {
  return [...companies.value].sort((a, b) => {
    if (!a.start_date) return 1
    if (!b.start_date) return -1
    return new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
  })
})

const displayProjects = computed(() => {
  return projects.value.length > 0 ? projects.value : staticProjects
})

// Methods
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  })
}

const parseTechnologies = (technologies: string | string[] | null | undefined): string[] => {
  if (!technologies) return []
  // If already an array, return as-is
  if (Array.isArray(technologies)) return technologies
  // If string, try to parse as JSON
  try {
    const parsed = JSON.parse(technologies)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// Load data on mount
onMounted(async () => {
  loading.value = true
  try {
    await portfolioStore.fetchAllData()
  } catch (error) {
    logger.error('Error loading portfolio data:', error)
  } finally {
    loading.value = false
  }

  // Fetch documents
  documentsLoading.value = true
  try {
    documents.value = await getDocuments()
  } catch (error) {
    logger.error('Error loading documents:', error)
    documentsError.value = 'Failed to load publications'
  } finally {
    documentsLoading.value = false
  }

  // Register service worker for PWA
  if ('serviceWorker' in navigator) {
    try {
      await navigator.serviceWorker.register('/sw.js')
      logger.log('Service Worker registered successfully')
    } catch (error) {
      logger.error('Service Worker registration failed:', error)
    }
  }

  // Apply scroll animations to cards with staggered effect
  useBatchAnimation('.experience-card', {
    animation: 'slideUp',
    duration: 600,
    delay: 0,
    stagger: 150,
    threshold: 0.1
  })

  useBatchAnimation('.education-card', {
    animation: 'slideUp',
    duration: 600,
    delay: 0,
    stagger: 150,
    threshold: 0.1
  })

  useBatchAnimation('.project-card', {
    animation: 'slideUp',
    duration: 600,
    delay: 0,
    stagger: 150,
    threshold: 0.1
  })

  useBatchAnimation('.section-title', {
    animation: 'fadeIn',
    duration: 800,
    delay: 0,
    threshold: 0.2
  })
})
</script>

<style scoped>
/* Import custom styles */
@import '../assets/portfolio.css';

/* Additional Vue-specific styles */
.portfolio-home {
  padding-top: 0;
}

/* Smooth scrolling */
html {
  scroll-behavior: smooth;
}

/* Ensure navbar is above content */
:deep(.navbar-custom) {
  z-index: 1000;
}

/* Company and Education logo layout */
.company-header-with-logo,
.education-header-with-logo {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.card-logo {
  width: 56px;
  height: 56px;
  object-fit: contain;
  margin-right: 1rem;
  min-width: 56px;
  border-radius: 8px;
  flex-shrink: 0;
  background: #fff;
  padding: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.company-header-content {
  flex: 1;
}

/* Documents grid */
.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

/* Loading and error states */
.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
}

.error-state {
  color: #ff6b6b;
}

/* Experience Card Improvements */
.experience-card {
  border-left: 4px solid var(--primary-500);
}

.experience-card:hover {
  border-left-color: var(--primary-600);
}

/* Education Card Improvements */
.education-card {
  text-align: center;
}

.education-header-with-logo {
  flex-direction: column;
  align-items: center;
}

.education-header-with-logo .card-logo {
  width: 72px;
  height: 72px;
  margin-right: 0;
  margin-bottom: 1rem;
}

.education-institution {
  text-align: center;
}

.education-degree {
  text-align: center;
}

/* Project Card Improvements */
.project-card {
  display: flex;
  flex-direction: column;
}

.project-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.project-links {
  margin-top: auto;
  padding-top: 1rem;
}

@media (max-width: 768px) {
  .documents-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .card-logo {
    width: 48px;
    height: 48px;
    min-width: 48px;
  }

  .education-header-with-logo .card-logo {
    width: 64px;
    height: 64px;
  }
}

/* About Section Layout */
.about-layout {
  display: flex;
  align-items: flex-start;
  gap: 3rem;
  max-width: 1000px;
  margin: 0 auto;
}

.profile-photo-container {
  flex-shrink: 0;
}

.profile-photo {
  width: 280px;
  height: auto;
  border-radius: 12px;
  object-fit: cover;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
}

.profile-photo:hover {
  transform: scale(1.02);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

.about-text {
  flex: 1;
  text-align: left;
}

.about-text p {
  margin-bottom: 1rem;
  line-height: 1.7;
}

.about-text ul {
  padding-left: 1.5rem;
  margin-bottom: 1.5rem;
}

.about-text li {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

[data-theme='dark'] .profile-photo {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

[data-theme='dark'] .profile-photo:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
}

@media (max-width: 768px) {
  .about-layout {
    flex-direction: column;
    align-items: center;
    gap: 2rem;
  }

  .profile-photo {
    width: 200px;
  }

  .about-text {
    text-align: center;
  }

  .about-text ul {
    text-align: left;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }
}
</style>
