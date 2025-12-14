<template>
  <div class="company-detail-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading company details...</span>
      </div>
      <p class="mt-3">Loading company details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container alert alert-danger" role="alert">
      <h3>Error Loading Company Details</h3>
      <p>{{ error }}</p>
      <router-link to="/" class="btn btn-primary">Return to Home</router-link>
    </div>

    <!-- Company Detail Content -->
    <div v-else-if="company" class="company-detail-content">
      <!-- Breadcrumb Navigation -->
      <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <router-link to="/">Home</router-link>
          </li>
          <li class="breadcrumb-item">
            <a href="#experience" @click.prevent="scrollToSection('experience')">Experience</a>
          </li>
          <li class="breadcrumb-item active" aria-current="page">
            {{ company.name }}
          </li>
        </ol>
      </nav>

      <!-- Company Header -->
      <div class="company-header mb-5">
        <div class="d-flex align-items-center mb-3">
          <img
            v-if="company.logo_url"
            :src="company.logo_url"
            :alt="`${company.name} logo`"
            class="company-logo me-3"
            loading="lazy"
          />
          <div>
            <h1 class="company-name mb-2">{{ company.name }}</h1>
            <h2 class="company-title h4 text-muted mb-0">{{ company.title }}</h2>
          </div>
        </div>
        <p class="company-dates text-muted">
          {{ formatDate(company.start_date) }} - {{ formatDate(company.end_date) }}
          <span v-if="!company.end_date" class="badge bg-success ms-2">Current</span>
        </p>
      </div>

      <!-- Video and Map Section -->
      <div class="row g-4 mb-5">
        <!-- Video Embed -->
        <div v-if="company.video_url" class="col-lg-6">
          <VideoEmbed
            :url="company.video_url"
            :title="company.video_title || `${company.name} video`"
            :heading="company.video_title"
          />
        </div>

        <!-- Map Embed -->
        <div v-if="company.map_url" :class="company.video_url ? 'col-lg-6' : 'col-lg-12'">
          <MapEmbed
            :url="company.map_url"
            :title="company.map_title || `${company.name} location`"
            :heading="company.map_title"
          />
        </div>
      </div>

      <!-- Detailed Description -->
      <div class="detailed-description mb-5">
        <div class="description-content" v-html="formattedDescription"></div>
      </div>

      <!-- Technologies (if available) -->
      <div
        v-if="company.technologies && company.technologies.length > 0"
        class="technologies-section mb-5"
      >
        <h3 class="h5 mb-3">Technologies Used</h3>
        <div class="technologies-list">
          <span
            v-for="tech in company.technologies"
            :key="tech"
            class="badge bg-secondary me-2 mb-2"
          >
            {{ tech }}
          </span>
        </div>
      </div>

      <!-- Responsibilities (if available) -->
      <div
        v-if="company.responsibilities && company.responsibilities.length > 0"
        class="responsibilities-section mb-5"
      >
        <h3 class="h5 mb-3">Key Responsibilities</h3>
        <ul class="responsibilities-list">
          <li
            v-for="(responsibility, index) in company.responsibilities"
            :key="`resp-${index}-${responsibility.slice(0, 20)}`"
          >
            {{ responsibility }}
          </li>
        </ul>
      </div>

      <!-- Navigation Buttons -->
      <div class="navigation-buttons d-flex justify-content-between flex-wrap gap-3 mt-5">
        <router-link to="/" class="btn btn-outline-primary">
          <i class="bi bi-arrow-left me-2"></i>
          Back to Portfolio
        </router-link>

        <div class="experience-navigation d-flex gap-2 flex-wrap">
          <button
            v-if="previousCompany"
            class="btn btn-outline-secondary"
            :aria-label="`Previous: ${previousCompany.name}`"
            @click="navigateToCompany(previousCompany.id)"
          >
            <i class="bi bi-chevron-left me-1"></i>
            {{ previousCompany.name }}
          </button>

          <button
            v-if="nextCompany"
            class="btn btn-outline-secondary"
            :aria-label="`Next: ${nextCompany.name}`"
            @click="navigateToCompany(nextCompany.id)"
          >
            {{ nextCompany.name }}
            <i class="bi bi-chevron-right ms-1"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Back to Top Button -->
    <BackToTop />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import VideoEmbed from '../components/VideoEmbed.vue'
import MapEmbed from '../components/MapEmbed.vue'
import BackToTop from '../components/BackToTop.vue'
import type { Company } from '../types/api'
import { apiLogger } from '../utils/logger'
import DOMPurify from 'dompurify'

// Get API URL from environment variables
const API_URL: string = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const route = useRoute()
const router = useRouter()

const company = ref<Company | null>(null)
const allCompanies = ref<Company[]>([])
const loading = ref<boolean>(true)
const error = ref<string | null>(null)

// Format date helper
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'Present'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
}

// Format detailed description with markdown-like formatting and XSS protection
const formattedDescription = computed<string>(() => {
  if (!company.value?.detailed_description) return ''

  let html: string = company.value.detailed_description

  // Convert **bold** to <strong>
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Convert paragraphs (separated by double newlines)
  html = html
    .split('\n\n')
    .map(para => `<p>${para.trim()}</p>`)
    .join('')

  // Sanitize HTML to prevent XSS attacks
  // Configure DOMPurify to only allow safe URL protocols
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'strong', 'em', 'br', 'ul', 'ol', 'li', 'a'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i
  })
})

// Get previous and next companies for navigation
const previousCompany = computed<Company | null>(() => {
  if (!allCompanies.value.length || !company.value) return null
  const currentIndex = allCompanies.value.findIndex(c => c.id === company.value!.id)
  // Handle case where company is not found in array (findIndex returns -1)
  if (currentIndex <= 0) return null
  return allCompanies.value[currentIndex - 1]
})

const nextCompany = computed<Company | null>(() => {
  if (!allCompanies.value.length || !company.value) return null
  const currentIndex = allCompanies.value.findIndex(c => c.id === company.value!.id)
  // Handle case where company is not found in array (findIndex returns -1)
  if (currentIndex === -1 || currentIndex >= allCompanies.value.length - 1) return null
  return allCompanies.value[currentIndex + 1]
})

// Fetch company details
const fetchCompanyDetails = async (companyId: string): Promise<void> => {
  try {
    loading.value = true
    error.value = null

    // Fetch all companies first (for navigation)
    const companiesResponse = await axios.get<Company[]>(`${API_URL}/api/v1/companies/`)
    allCompanies.value = companiesResponse.data.sort((a, b) => {
      return new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
    })

    // Find the specific company
    company.value = allCompanies.value.find(c => c.id === companyId) || null

    if (!company.value) {
      error.value = 'Company not found'
    }
  } catch (err) {
    apiLogger.error('Error fetching company details:', err)
    error.value = 'Failed to load company details. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Navigate to another company
const navigateToCompany = (companyId: string): void => {
  router.push({ name: 'company-detail', params: { id: companyId } })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Scroll to section on home page
const scrollToSection = (sectionId: string): void => {
  router.push({ path: '/', hash: `#${sectionId}` })
}

// Load company on mount
onMounted((): void => {
  fetchCompanyDetails(route.params.id as string)
})
</script>

<style scoped>
.company-detail-view {
  min-height: 100vh;
  padding: 2rem 1rem;
  background-color: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1e293b);
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.loading-container p {
  color: var(--text-secondary, #64748b);
}

.company-detail-content {
  max-width: 1000px;
  margin: 0 auto;
}

.company-header {
  border-bottom: 2px solid var(--border-color, #e2e8f0);
  padding-bottom: 1.5rem;
}

.company-logo {
  width: 64px;
  height: 64px;
  object-fit: contain;
  border-radius: 8px;
  background: #fff;
  padding: 4px;
}

.company-name {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
}

.company-title {
  font-weight: 500;
  color: var(--text-secondary, #64748b);
}

.company-dates {
  font-size: 1rem;
  color: var(--text-secondary, #64748b);
}

.description-content {
  font-size: 1.1rem;
  line-height: 1.8;
  color: var(--text-primary, #1e293b);
}

.description-content :deep(p) {
  margin-bottom: 1.5rem;
  color: var(--text-primary, #1e293b);
}

.description-content :deep(strong) {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

.technologies-section h3,
.responsibilities-section h3 {
  color: var(--text-primary, #1e293b);
}

.technologies-list .badge {
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
  font-weight: 500;
  background-color: var(--primary-500, #3b82f6) !important;
  color: #fff !important;
}

.responsibilities-list {
  list-style: disc;
  padding-left: 2rem;
}

.responsibilities-list li {
  margin-bottom: 0.75rem;
  line-height: 1.6;
  color: var(--text-primary, #1e293b);
}

.breadcrumb {
  background-color: transparent;
  padding: 0;
  margin-bottom: 1.5rem;
}

.breadcrumb-item a {
  text-decoration: none;
  color: var(--primary-500, #3b82f6);
}

.breadcrumb-item a:hover {
  text-decoration: underline;
}

.breadcrumb-item.active {
  color: var(--text-secondary, #64748b);
}

.navigation-buttons {
  border-top: 2px solid var(--border-color, #e2e8f0);
  padding-top: 2rem;
}

.experience-navigation button {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Responsive Design */
@media (max-width: 768px) {
  .company-name {
    font-size: 1.5rem;
  }

  .company-logo {
    width: 48px;
    height: 48px;
  }

  .navigation-buttons {
    flex-direction: column;
  }

  .experience-navigation {
    width: 100%;
    justify-content: space-between;
  }

  .experience-navigation button {
    flex: 1;
    max-width: none;
  }
}

/* Dark mode support */
[data-theme='dark'] .company-detail-view {
  background-color: var(--bg-primary, #0f172a);
  color: var(--text-primary, #f1f5f9);
}

[data-theme='dark'] .company-header {
  border-bottom-color: rgba(255, 255, 255, 0.15);
}

[data-theme='dark'] .company-name {
  color: #f1f5f9;
}

[data-theme='dark'] .company-title {
  color: #94a3b8;
}

[data-theme='dark'] .company-dates {
  color: #94a3b8;
}

[data-theme='dark'] .description-content,
[data-theme='dark'] .description-content :deep(p),
[data-theme='dark'] .description-content :deep(strong) {
  color: #e2e8f0;
}

[data-theme='dark'] .technologies-section h3,
[data-theme='dark'] .responsibilities-section h3 {
  color: #f1f5f9;
}

[data-theme='dark'] .technologies-list .badge {
  background-color: rgba(59, 130, 246, 0.3) !important;
  color: #93c5fd !important;
}

[data-theme='dark'] .responsibilities-list li {
  color: #e2e8f0;
}

[data-theme='dark'] .navigation-buttons {
  border-top-color: rgba(255, 255, 255, 0.15);
}

[data-theme='dark'] .breadcrumb-item a {
  color: #60a5fa;
}

[data-theme='dark'] .breadcrumb-item.active {
  color: #94a3b8;
}

[data-theme='dark'] .loading-container p {
  color: #94a3b8;
}

[data-theme='dark'] .btn-outline-primary {
  color: #60a5fa;
  border-color: #60a5fa;
}

[data-theme='dark'] .btn-outline-primary:hover {
  background-color: #60a5fa;
  color: #0f172a;
}

[data-theme='dark'] .btn-outline-secondary {
  color: #94a3b8;
  border-color: #475569;
}

[data-theme='dark'] .btn-outline-secondary:hover {
  background-color: #475569;
  color: #f1f5f9;
}
</style>
