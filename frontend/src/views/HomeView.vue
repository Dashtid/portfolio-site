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
              <div class="company-header">
                <h3 class="company-name">{{ company.name }}</h3>
                <span class="company-dates">{{ formatDate(company.start_date) }} - {{ company.end_date ? formatDate(company.end_date) : 'Present' }}</span>
              </div>
              <p class="job-title">{{ company.title }}</p>
              <p class="company-location">{{ company.location }}</p>
              <p class="company-description">{{ company.description }}</p>
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
            <h3 class="education-institution">{{ edu.institution }}</h3>
            <p class="education-degree"><strong>{{ edu.degree }}</strong></p>
            <p class="education-field" v-if="edu.field_of_study">{{ edu.field_of_study }}</p>
            <p class="education-description" v-if="edu.description">{{ edu.description }}</p>
            <p class="education-dates">{{ formatDate(edu.start_date) }} - {{ edu.end_date ? formatDate(edu.end_date) : 'Present' }}</p>
          </div>
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
    <section id="contact" class="portfolio-section">
      <div class="container">
        <div class="contact-content">
          <h2 class="section-title">
            <img src="/images/contact.svg" alt="Contact Icon" class="section-icon" loading="lazy" />
            Contact
          </h2>
          <div style="text-align: left; max-width: 400px; margin: 0 auto;">
            <p style="display: flex; align-items: center; margin-bottom: 1rem;">
              <strong>LinkedIn:</strong>
              <span style="margin-left: 1rem;">
                <a href="https://www.linkedin.com/in/david-dashti/" target="_blank" rel="noopener" style="color: var(--primary-600); text-decoration: none;">David Dashti</a>
              </span>
            </p>
            <p style="display: flex; align-items: center; margin-bottom: 1rem;">
              <strong>GitHub:</strong>
              <span style="margin-left: 1rem;">
                <a href="https://github.com/Dashtid" target="_blank" rel="noopener" style="color: var(--primary-600); text-decoration: none;">Dashtid</a>
              </span>
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer Section -->
    <FooterSection />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import NavBar from '../components/NavBar.vue'
import FooterSection from '../components/FooterSection.vue'
import GitHubStats from '../components/GitHubStats.vue'

const portfolioStore = usePortfolioStore()
const loading = ref(false)

// Computed properties for education from API
const education = computed(() => portfolioStore.education || [])

// Static projects data as fallback
const staticProjects = [
  {
    id: 1,
    name: "Portfolio Website",
    description: "Personal portfolio showcasing professional experience and projects",
    technologies: '["Vue.js", "Python", "FastAPI"]',
    github_url: "https://github.com/Dashtid"
  }
]

// Computed properties
const companies = computed(() => portfolioStore.companies || [])
const projects = computed(() => portfolioStore.projects || [])
const companiesByDate = computed(() => {
  return [...companies.value].sort((a, b) => {
    if (!a.start_date) return 1
    if (!b.start_date) return -1
    return new Date(b.start_date) - new Date(a.start_date)
  })
})

const displayProjects = computed(() => {
  return projects.value.length > 0 ? projects.value : staticProjects
})

// Methods
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  })
}

const parseTechnologies = (technologies) => {
  if (!technologies) return []
  try {
    return JSON.parse(technologies)
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

  // Register service worker for PWA
  if ('serviceWorker' in navigator) {
    try {
      await navigator.serviceWorker.register('/sw.js')
      console.log('Service Worker registered successfully')
    } catch (error) {
      console.error('Service Worker registration failed:', error)
    }
  }
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

/* Contact section specific styling */
.contact-section {
  background: var(--primary-600);
  color: white;
  padding: 4rem 0;
}

.contact-section .section-title {
  color: white;
}

.contact-section .section-title::after {
  background: white;
}

.contact-section p {
  color: rgba(255, 255, 255, 0.9);
}

.contact-section .contact-link {
  background: white;
  color: var(--primary-600);
  padding: 0.75rem 1.5rem;
  border-radius: 30px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  display: inline-block;
}

.contact-section .contact-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>