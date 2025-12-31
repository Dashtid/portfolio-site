<template>
  <div class="admin-education">
    <div class="admin-header">
      <h2>Manage Education & Certifications</h2>
      <button class="btn btn-primary" @click="showForm = true">Add New Education</button>
    </div>

    <!-- Add/Edit Form Modal -->
    <div
      v-if="showForm"
      ref="modalRef"
      class="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="education-modal-title"
      @click.self="closeForm"
      @keydown.escape="closeForm"
    >
      <div class="modal-content">
        <h3 id="education-modal-title">{{ editingEducation ? 'Edit' : 'Add' }} Education</h3>
        <form @submit.prevent="saveEducation">
          <div class="form-group">
            <label for="edu-institution">Institution *</label>
            <input
              id="edu-institution"
              v-model="formData.institution"
              type="text"
              class="form-control"
              required
            />
          </div>

          <div class="form-group">
            <label for="edu-degree">Degree/Certification *</label>
            <input
              id="edu-degree"
              v-model="formData.degree"
              type="text"
              class="form-control"
              required
            />
          </div>

          <div class="form-group">
            <label for="edu-field">Field of Study</label>
            <input
              id="edu-field"
              v-model="formData.field_of_study"
              type="text"
              class="form-control"
            />
          </div>

          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label for="edu-start-date">Start Date</label>
                <input
                  id="edu-start-date"
                  v-model="formData.start_date"
                  type="date"
                  class="form-control"
                />
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <label for="edu-end-date">End Date</label>
                <input
                  id="edu-end-date"
                  v-model="formData.end_date"
                  type="date"
                  class="form-control"
                />
              </div>
            </div>
          </div>

          <div class="form-group">
            <label for="edu-location">Location</label>
            <input id="edu-location" v-model="formData.location" type="text" class="form-control" />
          </div>

          <div class="form-group">
            <label for="edu-description">Description</label>
            <textarea
              id="edu-description"
              v-model="formData.description"
              class="form-control"
              rows="3"
            ></textarea>
          </div>

          <div class="form-check mb-3">
            <input
              id="is_certification"
              v-model="formData.is_certification"
              type="checkbox"
              class="form-check-input"
            />
            <label class="form-check-label" for="is_certification"> This is a certification </label>
          </div>

          <div v-if="formData.is_certification" class="form-group">
            <label for="edu-cert-number">Certificate Number</label>
            <input
              id="edu-cert-number"
              v-model="formData.certificate_number"
              type="text"
              class="form-control"
            />
          </div>

          <div class="form-group">
            <label for="edu-order">Display Order</label>
            <input
              id="edu-order"
              v-model.number="formData.order"
              type="number"
              class="form-control"
              min="0"
            />
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="closeForm">Cancel</button>
            <button type="submit" class="btn btn-primary">
              {{ editingEducation ? 'Update' : 'Add' }} Education
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Education List -->
    <div class="education-list">
      <h3>Degrees</h3>
      <div v-if="degrees.length" class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Institution</th>
              <th>Degree</th>
              <th>Field</th>
              <th>Dates</th>
              <th>Order</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="edu in degrees" :key="edu.id">
              <td>{{ edu.institution }}</td>
              <td>{{ edu.degree }}</td>
              <td>{{ edu.field_of_study || '-' }}</td>
              <td>
                {{ formatDate(edu.start_date) }} -
                {{ edu.end_date ? formatDate(edu.end_date) : 'Present' }}
              </td>
              <td>{{ edu.order }}</td>
              <td>
                <button class="btn btn-sm btn-warning me-2" @click="editEducation(edu)">
                  Edit
                </button>
                <button class="btn btn-sm btn-danger" @click="deleteEducation(edu.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-muted">No degrees added yet.</p>

      <h3 class="mt-4">Certifications</h3>
      <div v-if="certifications.length" class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Institution</th>
              <th>Certification</th>
              <th>Certificate #</th>
              <th>Date</th>
              <th>Order</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cert in certifications" :key="cert.id">
              <td>{{ cert.institution }}</td>
              <td>{{ cert.degree }}</td>
              <td>{{ cert.certificate_number || '-' }}</td>
              <td>{{ cert.end_date ? formatDate(cert.end_date) : '-' }}</td>
              <td>{{ cert.order }}</td>
              <td>
                <button class="btn btn-sm btn-warning me-2" @click="editEducation(cert)">
                  Edit
                </button>
                <button class="btn btn-sm btn-danger" @click="deleteEducation(cert.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-muted">No certifications added yet.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
import api from '../../api/client'
import { apiLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'
import { useFocusTrap } from '@/composables/useFocusTrap'

// Toast notifications
const toast = useToast()

// Modal focus trap for accessibility
const modalRef = ref<HTMLElement | null>(null)
const { activate: activateFocusTrap, deactivate: deactivateFocusTrap } = useFocusTrap(modalRef)

// Education form interface
interface EducationFormData {
  id?: string
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string
  location: string
  description: string
  is_certification: boolean
  certificate_number: string
  order: number
}

const authStore = useAuthStore()
const router = useRouter()

const showForm = ref<boolean>(false)
const editingEducation = ref<EducationFormData | null>(null)
const educationList = ref<EducationFormData[]>([])

const formData = ref<EducationFormData>({
  institution: '',
  degree: '',
  field_of_study: '',
  start_date: '',
  end_date: '',
  location: '',
  description: '',
  is_certification: false,
  certificate_number: '',
  order: 0
})

// AbortController for request cancellation
let abortController: AbortController | null = null

// Computed properties
const degrees = computed<EducationFormData[]>(() =>
  educationList.value.filter(e => !e.is_certification)
)
const certifications = computed<EducationFormData[]>(() =>
  educationList.value.filter(e => e.is_certification)
)

// Methods
const fetchEducation = async (): Promise<void> => {
  // Cancel any pending request
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()

  try {
    const response = await api.get<EducationFormData[]>('/education/', {
      signal: abortController.signal
    })
    educationList.value = response.data
  } catch (error) {
    // Ignore cancelled requests
    if (axios.isCancel(error)) return
    apiLogger.error('Error fetching education:', error)
  }
}

const saveEducation = async (): Promise<void> => {
  try {
    if (editingEducation.value) {
      await api.put(`/education/${editingEducation.value.id}/`, formData.value)
      toast.success('Education updated successfully')
    } else {
      await api.post('/education/', formData.value)
      toast.success('Education added successfully')
    }
    await fetchEducation()
    closeForm()
  } catch (error) {
    apiLogger.error('Error saving education:', error)
    toast.error('Failed to save education')
  }
}

const editEducation = (edu: EducationFormData): void => {
  editingEducation.value = edu
  formData.value = { ...edu }
  showForm.value = true
}

const deleteEducation = async (id: string | undefined): Promise<void> => {
  if (!id) return
  if (!confirm('Are you sure you want to delete this education record?')) return

  try {
    await api.delete(`/education/${id}/`)
    toast.success('Education deleted successfully')
    await fetchEducation()
  } catch (error) {
    apiLogger.error('Error deleting education:', error)
    toast.error('Failed to delete education')
  }
}

const closeForm = (): void => {
  deactivateFocusTrap()
  showForm.value = false
  editingEducation.value = null
  formData.value = {
    institution: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: '',
    location: '',
    description: '',
    is_certification: false,
    certificate_number: '',
    order: 0
  }
}

// Watch for modal visibility to manage focus trap
watch(showForm, isOpen => {
  if (isOpen) {
    activateFocusTrap()
  }
})

const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  // Check for Invalid Date
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  })
}

// Check authentication on mount
onMounted(async (): Promise<void> => {
  if (!authStore.isAuthenticated) {
    router.push('/admin/login')
    return
  }

  await fetchEducation()
})

// Cancel pending requests on unmount
onUnmounted(() => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
})
</script>

<style scoped>
.admin-education {
  padding: 2rem;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

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
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--color-gray-300, #dee2e6);
  border-radius: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.education-list h3 {
  margin-top: 2rem;
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.table {
  width: 100%;
  margin-bottom: 1rem;
  background-color: transparent;
}

.table th {
  padding: 0.75rem;
  vertical-align: top;
  border-top: 1px solid var(--color-gray-300, #dee2e6);
  font-weight: 600;
  color: var(--color-gray-900, #1f2937);
}

.table td {
  padding: 0.75rem;
  vertical-align: top;
  border-top: 1px solid var(--color-gray-300, #dee2e6);
  color: var(--color-gray-700, #374151);
}

@media (max-width: 768px) {
  .admin-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .table-responsive {
    overflow-x: auto;
  }
}

/* Dark Mode */
[data-theme='dark'] .admin-education {
  background: var(--bg-primary, #0f172a);
}

[data-theme='dark'] .admin-education h2,
[data-theme='dark'] .admin-education h3 {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .modal-content {
  background: var(--bg-secondary, #1e293b);
}

[data-theme='dark'] .form-group label {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .form-control {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .modal-overlay {
  background: rgba(0, 0, 0, 0.7);
}

[data-theme='dark'] .form-control:focus {
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.4);
}

/* Focus visible states for buttons */
.btn:focus-visible {
  outline: 2px solid var(--color-primary, #2563eb);
  outline-offset: 2px;
}

[data-theme='dark'] .btn:focus-visible {
  outline-color: var(--primary-400, #60a5fa);
}

/* Checkbox focus styles */
.form-check-input:focus {
  border-color: var(--primary-500, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

[data-theme='dark'] .form-check-input {
  background-color: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .form-check-input:focus {
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.35);
}

[data-theme='dark'] .form-check-input:checked {
  background-color: var(--primary-500, #3b82f6);
  border-color: var(--primary-500, #3b82f6);
}

[data-theme='dark'] .form-check-label {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .table {
  background: var(--bg-secondary, #1e293b);
}

[data-theme='dark'] .table th {
  color: var(--text-primary, #f8fafc);
  border-top-color: var(--border-primary, #475569);
}

[data-theme='dark'] .table td {
  color: var(--text-secondary, #cbd5e1);
  border-top-color: var(--border-primary, #475569);
}

[data-theme='dark'] .text-muted {
  color: var(--text-tertiary, #94a3b8) !important;
}
</style>
