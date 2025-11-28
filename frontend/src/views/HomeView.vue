<template>
  <div class="portfolio-home">
    <!-- Navigation Bar -->
    <NavBar />

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
          <img src="/images/experience.svg" alt="Experience Icon" class="section-icon" loading="lazy" />
          Experience
        </h2>
        <div class="experience-list">
          <!-- Dynamic content from backend or static fallback -->
          <template v-if="companies.length">
            <div v-for="company in companiesByDate" :key="company.id" class="experience-card fade-in">
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
                    <span class="company-dates">{{ formatDate(company.start_date) }} - {{ company.end_date ? formatDate(company.end_date) : 'Present' }}</span>
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
              <p class="company-description">Leading cybersecurity initiatives and developing innovative healthcare solutions.</p>
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- Education Section -->
    <section id="education" class="portfolio-section bg-light">
      <div class="container">
        <h2 class="section-title">
          <img src="/images/education.svg" alt="Education Icon" class="section-icon" loading="lazy" />
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
                <p class="education-degree"><strong>{{ edu.degree }}</strong></p>
              </div>
            </div>
            <p class="education-field" v-if="edu.field_of_study">{{ edu.field_of_study }}</p>
            <p class="education-description" v-if="edu.description">{{ edu.description }}</p>
            <p class="education-dates">{{ formatDate(edu.start_date) }} - {{ edu.end_date ? formatDate(edu.end_date) : 'Present' }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Publications/Research Section -->
    <section id="publications" class="portfolio-section bg-dark">
      <div class="container">
        <h2 class="section-title">
          <img src="/images/document.svg" alt="Publications Icon" class="section-icon" loading="lazy" />
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

        <!-- GitHub Stats Component -->
        <GitHubStats username="Dashtid" />

        <div class="projects-grid">
          <div v-for="project in displayProjects" :key="project.id || project.name" class="project-card fade-in">
            <div class="project-content">
              <h3 class="project-title">{{ project.name }}</h3>
              <p class="project-description">{{ project.description }}</p>
              <div v-if="project.technologies" class="project-tech">
                <span v-for="tech in parseTechnologies(project.technologies)" :key="tech" class="tech-badge">
                  {{ tech }}
                </span>
              </div>
              <div class="project-links">
                <a v-if="project.github_url" :href="project.github_url" target="_blank" class="project-link">View on GitHub</a>
                <a v-if="project.live_url" :href="project.live_url" target="_blank" class="project-link">Live Demo</a>
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
        <div class="about-content">
          <p>
            I am a biomedical engineer specializing in cybersecurity and regulatory compliance for medical software
            and AI systems. As a QA/RA & Security Specialist at Hermes Medical Solutions, I ensure that our
            software and digital health solutions meet the highest standards of security, privacy, and regulatory
            alignment (NIS2, ISO 27001, EU AI Act).
          </p>
          <p><strong>Current focus areas:</strong></p>
          <ul style="text-align: left; max-width: 600px; margin: 0 auto 2rem;">
            <li>Cybersecurity governance in medical software development</li>
            <li>Ensuring compliance with NIS2 and ISO 27001</li>
            <li>Supporting market clearance for medical software (MDR, GDPR)</li>
            <li>Preparing frameworks for AI Act compliance in healthcare AI systems</li>
          </ul>
          <p>
            <strong>Technical skills:</strong> Windows Server, Unix/Linux, Docker, PowerShell scripting, Bash
            scripting, Python, Git
          </p>
          <p>
            I am passionate about making healthcare technology safer and more trustworthy by protecting patient
            data, ensuring system integrity, and helping organizations navigate the new AI regulatory landscape.
          </p>
        </div>
      </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="portfolio-section contact-section-styled">
      <div class="container">
        <h2 class="section-title">
          <img src="/images/contact.svg" alt="Contact Icon" class="section-icon" loading="lazy" />
          Get In Touch
        </h2>
        <div class="contact-content-styled">
          <p class="contact-intro">
            Interested in discussing cybersecurity, medical software compliance, or potential collaborations?
            Feel free to reach out through any of the channels below.
          </p>
          <div class="contact-cards">
            <a href="https://www.linkedin.com/in/david-dashti/" target="_blank" rel="noopener" class="contact-card-item">
              <div class="contact-card-icon linkedin">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
              </div>
              <span class="contact-card-label">LinkedIn</span>
              <span class="contact-card-handle">David Dashti</span>
            </a>
            <a href="https://github.com/Dashtid" target="_blank" rel="noopener" class="contact-card-item">
              <div class="contact-card-icon github">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </div>
              <span class="contact-card-label">GitHub</span>
              <span class="contact-card-handle">@Dashtid</span>
            </a>
          </div>
        </div>
      </div>
    </section>

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
import GitHubStats from '../components/GitHubStats.vue'
import BackToTop from '../components/BackToTop.vue'
import DocumentCard from '../components/DocumentCard.vue'
import { useBatchAnimation } from '../composables/useScrollAnimations'
import { getDocuments } from '../api/services'
import type { Document } from '../types/api'

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
    name: "Portfolio Website",
    description: "Personal portfolio showcasing professional experience and projects",
    technologies: ["Vue.js", "Python", "FastAPI"],
    github_url: "https://github.com/Dashtid",
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
    console.error('Error loading portfolio data:', error)
  } finally {
    loading.value = false
  }

  // Fetch documents
  documentsLoading.value = true
  try {
    documents.value = await getDocuments()
  } catch (error) {
    console.error('Error loading documents:', error)
    documentsError.value = 'Failed to load publications'
  } finally {
    documentsLoading.value = false
  }

  // Register service worker for PWA
  if ('serviceWorker' in navigator) {
    try {
      await navigator.serviceWorker.register('/sw.js')
      console.log('Service Worker registered successfully')
    } catch (error) {
      console.error('Service Worker registration failed:', error)
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

/* Contact Section Styled */
.contact-section-styled {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
  color: white;
}

.contact-section-styled .section-title {
  color: white !important;
}

.contact-section-styled .section-title::after {
  background: rgba(255, 255, 255, 0.5) !important;
}

.contact-section-styled .section-icon {
  filter: brightness(0) invert(1);
}

.contact-content-styled {
  text-align: center;
  max-width: 700px;
  margin: 0 auto;
}

.contact-intro {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2.5rem;
  line-height: 1.7;
}

.contact-cards {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.contact-card-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 2rem 3rem;
  text-decoration: none;
  color: white;
  transition: all 0.3s ease;
  min-width: 180px;
}

.contact-card-item:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}

.contact-card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  transition: transform 0.3s ease;
}

.contact-card-icon.linkedin {
  background: #0077b5;
}

.contact-card-icon.github {
  background: #333;
}

.contact-card-item:hover .contact-card-icon {
  transform: scale(1.1);
}

.contact-card-label {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.8;
  margin-bottom: 0.25rem;
}

.contact-card-handle {
  font-size: 1.125rem;
  font-weight: 600;
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

/* About Section Improvements */
.about-content ul {
  text-align: left;
  max-width: 600px;
  margin: 0 auto 2rem;
  padding-left: 1.5rem;
}

.about-content li {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
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

  .contact-cards {
    flex-direction: column;
    align-items: center;
  }

  .contact-card-item {
    width: 100%;
    max-width: 280px;
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
</style>