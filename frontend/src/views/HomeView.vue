<template>
  <div class="portfolio-home">
    <!-- Navigation Bar -->
    <NavBar />

    <!-- Hero Section with Stockholm Background -->
    <section id="hero" class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title fade-in">David Dashti</h1>
        <p class="hero-subtitle fade-in">Security & Technology Professional</p>
        <p class="hero-subtitle fade-in">Bridging Healthcare Innovation with Cybersecurity Excellence</p>
      </div>
    </section>

    <!-- Experience Section -->
    <section id="experience" class="portfolio-section">
      <div class="container">
        <h2 class="section-title">Professional Experience</h2>
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
    <section id="education" class="portfolio-section">
      <div class="container">
        <h2 class="section-title">Education</h2>
        <div class="education-grid">
          <div v-for="edu in educationList" :key="edu.id" class="education-card fade-in">
            <h3 class="education-institution">{{ edu.institution }}</h3>
            <p class="education-degree">{{ edu.degree }}</p>
            <p class="education-dates">{{ edu.dates }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="portfolio-section">
      <div class="container">
        <h2 class="section-title">GitHub Projects</h2>
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
        <h2 class="section-title">About Me</h2>
        <div class="about-content">
          <p>
            I am a Security Specialist and System Developer at Hermes Medical Solutions, where I combine my expertise
            in cybersecurity with medical technology innovation. With a Master's degree in Medical Engineering from KTH
            and hands-on experience across healthcare institutions, I bridge the gap between technology and healthcare.
          </p>
          <p>
            My focus areas include vulnerability management, DevSecOps practices, and building secure healthcare solutions.
            I'm passionate about leveraging technology to improve healthcare delivery while maintaining the highest security standards.
          </p>
        </div>
      </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="portfolio-section contact-section">
      <div class="container">
        <div class="contact-content">
          <h2 class="section-title">Get In Touch</h2>
          <p>Feel free to reach out for collaborations or opportunities</p>
          <div class="contact-links">
            <a href="https://github.com/Dashtid" target="_blank" class="contact-link">GitHub</a>
            <a href="https://linkedin.com/in/david-dashti" target="_blank" class="contact-link">LinkedIn</a>
            <a href="mailto:david@dashti.se" class="contact-link">Email</a>
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

const portfolioStore = usePortfolioStore()
const loading = ref(false)

// Static education data
const educationList = [
  {
    id: 1,
    institution: "KTH Royal Institute of Technology",
    degree: "M.Sc. Medical Engineering",
    dates: "2017 - 2022"
  },
  {
    id: 2,
    institution: "Lund University (LTH)",
    degree: "B.Sc. Biomedical Engineering (Exchange)",
    dates: "2020 - 2021"
  },
  {
    id: 3,
    institution: "Företagsuniversitetet",
    degree: "Business Management Certificate",
    dates: "2023"
  },
  {
    id: 4,
    institution: "CompTIA",
    degree: "Security+ Certification",
    dates: "2024"
  }
]

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