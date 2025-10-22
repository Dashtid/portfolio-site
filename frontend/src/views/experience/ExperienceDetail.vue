<template>
  <div class="experience-detail">
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-light bg-light sticky-top mb-4">
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

        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link to="/" class="nav-link px-3 py-2 border rounded shadow-sm">
                Home
              </router-link>
            </li>
          </ul>

          <!-- Experience Navigation -->
          <div class="d-flex gap-2 flex-wrap" v-if="allCompanies.length > 0">
            <router-link
              v-for="comp in allCompanies"
              :key="comp.id"
              :to="`/experience/${comp.id}`"
              class="nav-link px-2 py-1 border rounded shadow-sm text-center"
              :class="{ 'active': comp.id === companyId }"
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
        <hr>
        <router-link to="/" class="btn btn-primary">Return to Home</router-link>
      </div>
    </div>

    <!-- Company Details -->
    <main v-else-if="company" class="container py-5">
      <!-- Media Section: Video and Map -->
      <div class="row g-4 mb-5" v-if="company.video_url || company.map_url">
        <!-- YouTube Video -->
        <div class="col-lg-6" v-if="company.video_url">
          <h2>{{ company.video_title || `${company.name} Video` }}</h2>
          <div class="ratio ratio-16x9">
            <iframe
              :src="company.video_url"
              :title="company.video_title || `${company.name} Video`"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerpolicy="strict-origin-when-cross-origin"
              allowfullscreen
            ></iframe>
          </div>
        </div>

        <!-- Google Maps -->
        <div class="col-lg-6" v-if="company.map_url">
          <h2>{{ company.map_title || `${company.name} Location` }}</h2>
          <div class="ratio ratio-16x9">
            <iframe
              :src="company.map_url"
              :title="company.map_title || `${company.name} Location Map`"
              allowfullscreen
              loading="lazy"
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
            style="width: 64px; height: 64px; object-fit: contain;"
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
        <div v-html="formatDescription(company.description)"></div>
      </div>

      <!-- Detailed Description -->
      <div v-if="company.detailed_description" class="mb-5">
        <h3>Role & Responsibilities</h3>
        <div v-html="formatDescription(company.detailed_description)"></div>
      </div>

      <!-- Responsibilities List -->
      <div v-if="company.responsibilities && company.responsibilities.length > 0" class="mb-5">
        <h3>Key Responsibilities</h3>
        <ul class="list-group list-group-flush">
          <li
            v-for="(responsibility, index) in company.responsibilities"
            :key="index"
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
          <span
            v-for="(tech, index) in company.technologies"
            :key="index"
            class="badge bg-primary"
          >
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

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const company = ref(null)
const allCompanies = ref([])
const loading = ref(true)
const error = ref(null)

const companyId = computed(() => route.params.id)

// Format date helper
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

// Format description with HTML (sanitized from backend)
const formatDescription = (desc) => {
  if (!desc) return ''
  // Replace newlines with paragraph breaks
  return desc.split('\n\n').map(p => `<p>${p}</p>`).join('')
}

// Fetch all companies for navigation
const fetchAllCompanies = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/v1/companies/`)
    allCompanies.value = response.data.sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
  } catch (err) {
    console.error('Error fetching companies:', err)
  }
}

// Fetch company details
const fetchCompany = async (id) => {
  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/v1/companies/${id}`)
    company.value = response.data
  } catch (err) {
    console.error('Error fetching company:', err)
    if (err.response?.status === 404) {
      error.value = 'Company not found. It may have been removed or the link is incorrect.'
    } else {
      error.value = 'Failed to load company details. Please try again later.'
    }
  } finally {
    loading.value = false
  }
}

// Watch for route changes
watch(() => route.params.id, (newId) => {
  if (newId) {
    fetchCompany(newId)
  }
})

// Initial load
onMounted(() => {
  fetchAllCompanies()
  if (companyId.value) {
    fetchCompany(companyId.value)
  }
})
</script>

<style scoped>
.experience-detail {
  min-height: 100vh;
}

.nav-link.active {
  background-color: #2563eb;
  color: white !important;
  border-color: #2563eb !important;
}

.badge {
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
}

.list-group-item {
  border-left: none;
  border-right: none;
  padding-left: 0;
}

.list-group-item:first-child {
  border-top: none;
}

.ratio iframe {
  border: none;
  border-radius: 0.5rem;
}

h1, h2, h3 {
  color: #1e293b;
}

.text-muted {
  color: #64748b !important;
}
</style>
