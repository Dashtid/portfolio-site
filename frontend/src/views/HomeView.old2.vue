<template>
  <div class="portfolio-home">
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
          <!-- Hermes Medical Solutions -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">Hermes Medical Solutions</h3>
              <span class="company-dates">Sep 2022 - Present</span>
            </div>
            <p class="job-title">Security Specialist & System Developer</p>
            <p class="company-location">Stockholm, Sweden</p>
            <p class="company-description">Leading cybersecurity initiatives and developing innovative healthcare solutions in a medical technology environment.</p>
          </div>

          <!-- Karolinska University Hospital -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">Karolinska University Hospital</h3>
              <span class="company-dates">Jul 2020 - Nov 2021</span>
            </div>
            <p class="job-title">Medical Engineering Intern</p>
            <p class="company-location">Stockholm, Sweden</p>
            <p class="company-description">Supported medical technology operations and gained hands-on experience with healthcare systems.</p>
          </div>

          <!-- South General Hospital -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">South General Hospital (SöS)</h3>
              <span class="company-dates">Jul 2019 - Jul 2019</span>
            </div>
            <p class="job-title">Medical Engineering Intern</p>
            <p class="company-location">Stockholm, Sweden</p>
            <p class="company-description">Assisted with medical device maintenance and technical support.</p>
          </div>

          <!-- Softpro AB -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">Softpro AB</h3>
              <span class="company-dates">Apr 2019 - Jul 2019</span>
            </div>
            <p class="job-title">IT Support</p>
            <p class="company-location">Stockholm, Sweden</p>
            <p class="company-description">Provided technical support and IT infrastructure maintenance.</p>
          </div>

          <!-- Philips Healthcare -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">Philips Healthcare</h3>
              <span class="company-dates">Nov 2018 - Mar 2019</span>
            </div>
            <p class="job-title">Medical Engineering Intern</p>
            <p class="company-location">Stockholm, Sweden</p>
            <p class="company-description">Worked with medical imaging systems and healthcare technology solutions.</p>
          </div>

          <!-- Scania Group -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">Scania Group</h3>
              <span class="company-dates">Aug 2015 - Dec 2015</span>
            </div>
            <p class="job-title">Production Intern</p>
            <p class="company-location">Södertälje, Sweden</p>
            <p class="company-description">Gained experience in industrial production and quality control processes.</p>
          </div>

          <!-- Swedish Defence Forces -->
          <div class="experience-card fade-in">
            <div class="company-header">
              <h3 class="company-name">Swedish Defence Forces (FBU)</h3>
              <span class="company-dates">Aug 2014 - May 2015</span>
            </div>
            <p class="job-title">Military Service</p>
            <p class="company-location">Sweden</p>
            <p class="company-description">Completed mandatory military service, developing leadership and discipline skills.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Education Section -->
    <section id="education" class="portfolio-section">
      <div class="container">
        <h2 class="section-title">Education</h2>
        <div class="education-grid">
          <div class="education-card fade-in">
            <h3 class="education-institution">KTH Royal Institute of Technology</h3>
            <p class="education-degree">M.Sc. Medical Engineering</p>
            <p class="education-dates">2017 - 2022</p>
          </div>
          <div class="education-card fade-in">
            <h3 class="education-institution">Lund University (LTH)</h3>
            <p class="education-degree">B.Sc. Biomedical Engineering (Exchange)</p>
            <p class="education-dates">2020 - 2021</p>
          </div>
          <div class="education-card fade-in">
            <h3 class="education-institution">Företagsuniversitetet</h3>
            <p class="education-degree">Business Management Certificate</p>
            <p class="education-dates">2023</p>
          </div>
          <div class="education-card fade-in">
            <h3 class="education-institution">CompTIA</h3>
            <p class="education-degree">Security+ Certification</p>
            <p class="education-dates">2024</p>
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
    <section id="contact" class="contact-section">
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const portfolioStore = usePortfolioStore()
const loading = ref(false)

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
const projects = computed(() => portfolioStore.projects || [])
const displayProjects = computed(() => {
  return projects.value.length > 0 ? projects.value : staticProjects
})

// Methods
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
    await portfolioStore.fetchProjects()
  } catch (error) {
    console.error('Error loading projects:', error)
  } finally {
    loading.value = false
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
</style>