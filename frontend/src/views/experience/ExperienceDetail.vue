<template>
  <div class="experience-detail">
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg sticky-top mb-4">
      <div class="container">
        <router-link to="/" class="navbar-brand">David Dashti</router-link>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div id="navbarNav" class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link to="/" class="nav-link px-3 py-2 border rounded shadow-sm">
                Home
              </router-link>
            </li>
          </ul>

          <!-- Experience Navigation -->
          <div v-if="allCompanies.length > 0" class="d-flex gap-2 flex-wrap">
            <router-link
              v-for="comp in allCompanies"
              :key="comp.id"
              :to="`/experience/${comp.id}`"
              class="nav-link px-2 py-1 border rounded shadow-sm text-center"
              :class="{ active: comp.id === companyId }"
            >
              {{ comp.name }}
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Loading State -->
    <div v-if="loading" class="container py-5 text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3">Loading experience details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="container py-5">
      <div class="alert alert-danger" role="alert">
        <h4 class="alert-heading">Error Loading Experience</h4>
        <p>{{ error }}</p>
        <hr />
        <router-link to="/" class="btn btn-primary">Return to Home</router-link>
      </div>
    </div>

    <!-- Company Details -->
    <main v-else-if="company" class="container py-5">
      <!-- Media Section: Video and Map -->
      <div v-if="company.video_url || company.map_url" class="row g-4 mb-5">
        <!-- YouTube Video -->
        <div v-if="company.video_url" class="col-lg-6">
          <h2>{{ company.video_title || `${company.name} Video` }}</h2>
          <div class="ratio ratio-16x9">
            <iframe
              :src="company.video_url"
              :title="company.video_title || `${company.name} Video`"
              allow="
                accelerometer;
                autoplay;
                clipboard-write;
                encrypted-media;
                gyroscope;
                picture-in-picture;
                web-share;
              "
              referrerpolicy="strict-origin-when-cross-origin"
              allowfullscreen
              loading="lazy"
            ></iframe>
          </div>
        </div>

        <!-- Google Maps -->
        <div v-if="company.map_url" class="col-lg-6">
          <h2>{{ company.map_title || `${company.name} Location` }}</h2>
          <div class="ratio ratio-16x9">
            <iframe
              :src="company.map_url"
              :title="company.map_title || `${company.name} Location Map`"
              allowfullscreen
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              class="border-0"
            ></iframe>
          </div>
        </div>
      </div>

      <!-- Company Information -->
      <div class="mb-5">
        <div class="d-flex align-items-center mb-3">
          <img
            v-if="company.logo_url"
            :src="company.logo_url"
            :alt="`${company.name} logo`"
            class="me-3"
            style="width: 64px; height: 64px; object-fit: contain"
          />
          <div>
            <h1 class="mb-1">{{ company.title }}</h1>
            <h3 class="text-muted mb-0">{{ company.name }}</h3>
          </div>
        </div>

        <p class="text-muted">
          <i class="bi bi-geo-alt"></i> {{ company.location }}
          <span v-if="company.start_date" class="ms-3">
            <i class="bi bi-calendar"></i>
            {{ formatDate(company.start_date) }} -
            {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
          </span>
        </p>

        <div class="mb-4">
          <a
            v-if="company.website"
            :href="company.website"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-outline-primary me-2"
          >
            <i class="bi bi-globe"></i> Visit Website
          </a>
        </div>
      </div>

      <!-- Description -->
      <div class="mb-5">
        <h3>About {{ company.name }}</h3>
        <!-- eslint-disable-next-line vue/no-v-html -- Content sanitized with DOMPurify -->
        <div v-html="formatDescription(company.description)"></div>
      </div>

      <!-- Detailed Description -->
      <div v-if="company.detailed_description" class="mb-5">
        <h3>Role & Responsibilities</h3>
        <!-- eslint-disable-next-line vue/no-v-html -- Content sanitized with DOMPurify -->
        <div v-html="formatDescription(company.detailed_description)"></div>
      </div>

      <!-- Responsibilities List -->
      <div v-if="company.responsibilities && company.responsibilities.length > 0" class="mb-5">
        <h3>Key Responsibilities</h3>
        <ul class="list-group list-group-flush">
          <li
            v-for="(responsibility, index) in company.responsibilities"
            :key="`responsibility-${index}-${responsibility.slice(0, 20)}`"
            class="list-group-item"
          >
            {{ responsibility }}
          </li>
        </ul>
      </div>

      <!-- Technologies -->
      <div v-if="company.technologies && company.technologies.length > 0" class="mb-5">
        <h3>Technologies & Tools</h3>
        <div class="d-flex flex-wrap gap-2">
          <span v-for="tech in company.technologies" :key="tech" class="badge bg-primary">
            {{ tech }}
          </span>
        </div>
      </div>

      <!-- Back Navigation -->
      <div class="mt-5 pt-4 border-top">
        <router-link to="/" class="btn btn-outline-secondary">
          <i class="bi bi-arrow-left"></i> Back to Portfolio
        </router-link>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios, { type AxiosError } from 'axios'
import type { Company } from '@/types'
import { apiLogger } from '../../utils/logger'
import { config } from '../../config'
import DOMPurify from 'dompurify'

const route = useRoute()

const company = ref<Company | null>(null)
const allCompanies = ref<Company[]>([])
const loading = ref<boolean>(true)
const error = ref<string | null>(null)

const companyId = computed<string>(() => route.params.id as string)

// Format date helper
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

// Format description with HTML and XSS protection
const formatDescription = (desc: string | null | undefined): string => {
  if (!desc) return ''
  // Replace newlines with paragraph breaks
  const html = desc
    .split('\n\n')
    .map(p => `<p>${p}</p>`)
    .join('')

  // Sanitize HTML to prevent XSS attacks
  // Configure DOMPurify to only allow safe URL protocols
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'strong', 'em', 'br', 'ul', 'ol', 'li', 'a'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i
  })
}

// Fetch all companies for navigation
const fetchAllCompanies = async (): Promise<void> => {
  try {
    const response = await axios.get<Company[]>(`${config.apiUrl}/api/v1/companies/`)
    allCompanies.value = response.data.sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0))
  } catch (err) {
    apiLogger.error('Error fetching companies:', err)
  }
}

// Fetch company details
const fetchCompany = async (id: string): Promise<void> => {
  loading.value = true
  error.value = null

  try {
    const response = await axios.get<Company>(`${config.apiUrl}/api/v1/companies/${id}`)
    company.value = response.data
  } catch (err) {
    apiLogger.error('Error fetching company:', err)
    const axiosError = err as AxiosError
    if (axiosError.response?.status === 404) {
      error.value = 'Company not found. It may have been removed or the link is incorrect.'
    } else {
      error.value = 'Failed to load company details. Please try again later.'
    }
  } finally {
    loading.value = false
  }
}

// Watch for route changes
watch(
  () => route.params.id,
  newId => {
    if (newId) {
      fetchCompany(newId as string)
    }
  }
)

// Initial load
onMounted(async (): Promise<void> => {
  // Fetch companies for navigation (errors handled internally)
  await fetchAllCompanies()
  // Fetch current company details if ID is provided
  if (companyId.value) {
    await fetchCompany(companyId.value)
  }
})
</script>

<style scoped>
.experience-detail {
  min-height: 100vh;
  background-color: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1e293b);
}

.navbar {
  background-color: var(--bg-secondary, #f8fafc) !important;
}

.navbar-brand {
  color: var(--text-primary, #1e293b) !important;
  font-weight: 600;
}

.nav-link {
  color: var(--text-primary, #1e293b) !important;
  background-color: var(--bg-primary, #ffffff);
}

.nav-link.active {
  background-color: #2563eb !important;
  color: white !important;
  border-color: #2563eb !important;
}

.nav-link:hover:not(.active) {
  background-color: var(--bg-secondary, #f1f5f9);
}

.badge {
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
}

.list-group-item {
  border-left: none;
  border-right: none;
  padding-left: 0;
  background-color: transparent;
  color: var(--text-primary, #1e293b);
}

.list-group-item:first-child {
  border-top: none;
}

.ratio iframe {
  border: none;
  border-radius: 0.5rem;
}

h1,
h2,
h3 {
  color: var(--text-primary, #1e293b);
}

.text-muted {
  color: var(--text-secondary, #64748b) !important;
}

main p {
  color: var(--text-primary, #1e293b);
}

main :deep(p) {
  color: var(--text-primary, #1e293b);
}

.border-top {
  border-color: var(--border-color, #e2e8f0) !important;
}

/* Dark mode support */
[data-theme='dark'] .experience-detail {
  background-color: var(--bg-primary, #0f172a);
  color: var(--text-primary, #f1f5f9);
}

[data-theme='dark'] .navbar {
  background-color: #1e293b !important;
}

[data-theme='dark'] .navbar-brand {
  color: #f1f5f9 !important;
}

[data-theme='dark'] .navbar-toggler-icon {
  filter: invert(1);
}

[data-theme='dark'] .nav-link {
  color: #e2e8f0 !important;
  background-color: #1e293b;
  border-color: #475569 !important;
}

[data-theme='dark'] .nav-link:hover:not(.active) {
  background-color: #334155;
}

[data-theme='dark'] h1,
[data-theme='dark'] h2,
[data-theme='dark'] h3 {
  color: var(--text-primary);
}

[data-theme='dark'] .text-muted {
  color: var(--text-tertiary) !important;
}

[data-theme='dark'] main p,
[data-theme='dark'] main :deep(p) {
  color: var(--text-secondary);
}

[data-theme='dark'] .list-group-item {
  color: var(--text-secondary);
  border-color: var(--border-primary);
}

[data-theme='dark'] .border-top {
  border-color: var(--border-primary) !important;
}

[data-theme='dark'] .btn-outline-primary {
  color: var(--link-color);
  border-color: var(--link-color);
}

[data-theme='dark'] .btn-outline-primary:hover {
  background-color: var(--primary-400);
  color: var(--bg-primary);
}

[data-theme='dark'] .btn-outline-secondary {
  color: var(--text-tertiary);
  border-color: var(--border-secondary);
}

[data-theme='dark'] .btn-outline-secondary:hover {
  background-color: var(--border-secondary);
  color: var(--text-primary);
}

[data-theme='dark'] .badge.bg-primary {
  background-color: rgba(59, 130, 246, 0.3) !important;
  color: var(--primary-300, #93c5fd) !important;
}

[data-theme='dark'] .alert-danger {
  background-color: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--color-error, #fca5a5);
}

[data-theme='dark'] .spinner-border.text-primary {
  color: var(--link-color) !important;
}

[data-theme='dark'] .container p.mt-3 {
  color: var(--text-tertiary);
}
</style>
