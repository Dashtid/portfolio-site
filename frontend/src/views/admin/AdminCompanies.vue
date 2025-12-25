<template>
  <div class="admin-companies">
    <div class="page-header">
      <h2 class="page-title">Manage Experience</h2>
      <button class="add-button" @click="showAddForm = true">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 4v16m8-8H4" />
        </svg>
        Add Company
      </button>
    </div>

    <!-- Companies List -->
    <div class="companies-grid">
      <div v-if="loading" class="loading-state">Loading companies...</div>

      <div v-else-if="companies.length === 0" class="empty-state">
        <p>No companies added yet.</p>
      </div>

      <div v-else class="company-cards">
        <div v-for="company in companies" :key="company.id" class="company-card">
          <div class="company-header">
            <h3 class="company-name">{{ company.name }}</h3>
            <div class="company-actions">
              <button class="action-btn edit-btn" @click="editCompany(company)">
                <svg
                  class="icon-sm"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
              <button class="action-btn delete-btn" @click="deleteCompany(company.id)">
                <svg
                  class="icon-sm"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M3 6h18m-2 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"
                  />
                </svg>
              </button>
            </div>
          </div>

          <p class="company-title">{{ company.title }}</p>
          <p class="company-duration">
            {{ formatDate(company.start_date) }} -
            {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
          </p>
          <p class="company-location">{{ company.location }}</p>
          <p class="company-description">{{ company.description }}</p>
        </div>
      </div>
    </div>

    <!-- Add/Edit Form Modal -->
    <div v-if="showAddForm || editingCompany" class="modal-overlay" @click.self="closeForm">
      <div class="modal-content">
        <h3 class="modal-title">
          {{ editingCompany ? 'Edit Company' : 'Add New Company' }}
        </h3>

        <form class="company-form" @submit.prevent="saveCompany">
          <div class="form-group">
            <label for="name">Company Name *</label>
            <input id="name" v-model="form.name" type="text" required class="form-input" />
          </div>

          <div class="form-group">
            <label for="title">Job Title *</label>
            <input id="title" v-model="form.title" type="text" required class="form-input" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="start_date">Start Date *</label>
              <input
                id="start_date"
                v-model="form.start_date"
                type="date"
                required
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="end_date">End Date</label>
              <input id="end_date" v-model="form.end_date" type="date" class="form-input" />
            </div>
          </div>

          <div class="form-group">
            <label for="location">Location</label>
            <input id="location" v-model="form.location" type="text" class="form-input" />
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <textarea
              id="description"
              v-model="form.description"
              rows="4"
              class="form-textarea"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="technologies">Technologies (comma-separated)</label>
            <input
              id="technologies"
              v-model="technologiesInput"
              type="text"
              placeholder="Python, FastAPI, Docker"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="order_index">Display Order</label>
            <input
              id="order_index"
              v-model.number="form.order_index"
              type="number"
              min="0"
              class="form-input"
            />
          </div>

          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="closeForm">Cancel</button>
            <button type="submit" class="btn-save">
              {{ editingCompany ? 'Update' : 'Add' }} Company
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, type WritableComputedRef } from 'vue'
import apiClient from '../../api/client'
import type { Company } from '@/types'
import { apiLogger } from '../../utils/logger'

// Form data interface (extends Company with order_index)
interface CompanyFormData {
  name: string
  title: string
  start_date: string
  end_date: string
  location: string
  description: string
  technologies: string[]
  order_index: number
}

// Data
const companies = ref<Company[]>([])
const loading = ref<boolean>(false)
const showAddForm = ref<boolean>(false)
const editingCompany = ref<Company | null>(null)

// Form data
const form = ref<CompanyFormData>({
  name: '',
  title: '',
  start_date: '',
  end_date: '',
  location: '',
  description: '',
  technologies: [],
  order_index: 0
})

// Computed
const technologiesInput: WritableComputedRef<string> = computed({
  get(): string {
    return Array.isArray(form.value.technologies) ? form.value.technologies.join(', ') : ''
  },
  set(value: string): void {
    form.value.technologies = value
      .split(',')
      .map(t => t.trim())
      .filter(t => t)
  }
})

// Methods
const fetchCompanies = async (): Promise<void> => {
  loading.value = true
  try {
    const response = await apiClient.get<Company[]>('/api/v1/companies')
    companies.value = response.data
  } catch (error) {
    apiLogger.error('Error fetching companies:', error)
    alert('Failed to load companies')
  } finally {
    loading.value = false
  }
}

const editCompany = (company: Company): void => {
  editingCompany.value = company
  form.value = {
    name: company.name,
    title: company.title,
    start_date: company.start_date,
    end_date: company.end_date || '',
    location: company.location || '',
    description: company.description,
    technologies: Array.isArray(company.technologies)
      ? company.technologies
      : JSON.parse((company.technologies as unknown as string) || '[]'),
    order_index: (company as Company & { order_index?: number }).order_index || 0
  }
}

const saveCompany = async (): Promise<void> => {
  try {
    const data = {
      ...form.value,
      technologies: JSON.stringify(form.value.technologies)
    }

    if (editingCompany.value) {
      // Update existing
      await apiClient.put(`/api/v1/companies/${editingCompany.value.id}`, data)
      alert('Company updated successfully')
    } else {
      // Create new
      await apiClient.post('/api/v1/companies', data)
      alert('Company added successfully')
    }

    closeForm()
    fetchCompanies()
  } catch (error) {
    apiLogger.error('Error saving company:', error)
    alert('Failed to save company')
  }
}

const deleteCompany = async (id: string): Promise<void> => {
  if (!confirm('Are you sure you want to delete this company?')) {
    return
  }

  try {
    await apiClient.delete(`/api/v1/companies/${id}`)
    alert('Company deleted successfully')
    fetchCompanies()
  } catch (error) {
    apiLogger.error('Error deleting company:', error)
    alert('Failed to delete company')
  }
}

const closeForm = (): void => {
  showAddForm.value = false
  editingCompany.value = null
  form.value = {
    name: '',
    title: '',
    start_date: '',
    end_date: '',
    location: '',
    description: '',
    technologies: [],
    order_index: 0
  }
}

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  })
}

// Lifecycle
onMounted((): void => {
  fetchCompanies()
})
</script>

<style scoped>
.admin-companies {
  padding: var(--spacing-4);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0;
}

.add-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.add-button:hover {
  background: var(--color-primary-dark, #1e40af);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.icon {
  width: 20px;
  height: 20px;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

/* Companies Grid */
.companies-grid {
  background: white;
  padding: var(--spacing-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-gray-200);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-gray-600);
}

.company-cards {
  display: grid;
  gap: var(--spacing-4);
}

.company-card {
  padding: var(--spacing-4);
  background: var(--color-gray-50);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-200);
  transition: all var(--transition-base) ease;
}

.company-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.company-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-2);
}

.company-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin: 0;
}

.company-actions {
  display: flex;
  gap: var(--spacing-2);
}

.action-btn {
  padding: var(--spacing-1);
  background: transparent;
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.edit-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.delete-btn:hover {
  background: var(--color-red-600, #dc2626);
  border-color: var(--color-red-600, #dc2626);
  color: white;
}

.company-title {
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  margin: 0 0 var(--spacing-1);
}

.company-duration {
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
  margin: 0 0 var(--spacing-1);
}

.company-location {
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
  margin: 0 0 var(--spacing-2);
}

.company-description {
  color: var(--color-gray-700);
  line-height: var(--line-height-relaxed);
  margin: 0;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-4);
}

.modal-content {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0 0 var(--spacing-4);
}

/* Form */
.company-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.form-group label {
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-700);
  margin-bottom: var(--spacing-1);
  font-size: var(--font-size-sm);
}

.form-input,
.form-textarea {
  padding: var(--spacing-2);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: border-color var(--transition-base) ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb, 37, 99, 235), 0.3);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-gray-200);
}

.btn-cancel,
.btn-save {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.btn-cancel {
  background: transparent;
  color: var(--color-gray-600);
  border: 1px solid var(--color-gray-300);
}

.btn-cancel:hover {
  background: var(--color-gray-100);
}

.btn-save {
  background: var(--color-primary);
  color: white;
  border: none;
}

.btn-save:hover {
  background: var(--color-primary-dark, #1e40af);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Responsive */
@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-content {
    padding: var(--spacing-4);
  }
}

/* Dark Mode */
[data-theme='dark'] .page-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .companies-grid {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .loading-state,
[data-theme='dark'] .empty-state {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .company-card {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .company-card:hover {
  border-color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .company-name {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .company-title {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .company-duration,
[data-theme='dark'] .company-location {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .company-description {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .action-btn {
  border-color: var(--border-primary, #475569);
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .modal-content {
  background: var(--bg-secondary, #1e293b);
}

[data-theme='dark'] .modal-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .form-group label {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .form-input,
[data-theme='dark'] .form-textarea {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .modal-overlay {
  background: rgba(0, 0, 0, 0.7);
}

[data-theme='dark'] .form-input:focus,
[data-theme='dark'] .form-textarea:focus {
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.4);
}

/* Focus visible states for action buttons */
.action-btn:focus-visible {
  outline: 2px solid var(--color-primary, #2563eb);
  outline-offset: 2px;
}

[data-theme='dark'] .action-btn:focus-visible {
  outline-color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .form-actions {
  border-top-color: var(--border-primary, #475569);
}

[data-theme='dark'] .btn-cancel {
  color: var(--text-secondary, #cbd5e1);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .btn-cancel:hover {
  background: var(--bg-tertiary, #334155);
}

[data-theme='dark'] .btn-save {
  background: var(--primary-600, #2563eb);
  color: white;
}

[data-theme='dark'] .btn-save:hover {
  background: var(--primary-500, #3b82f6);
}
</style>
