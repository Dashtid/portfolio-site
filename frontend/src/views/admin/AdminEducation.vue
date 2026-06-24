<template>
  <div class="admin-education">
    <div class="admin-header">
      <h2>Manage Education & Certifications</h2>
      <button class="btn-save btn-primary" @click="showForm = true">Add New Education</button>
    </div>

    <AdminFormModal
      :open="showForm"
      :title="`${editingEducation ? 'Edit' : 'Add'} Education`"
      title-id="education-modal-title"
      @close="closeForm"
    >
      <form @submit.prevent="saveEducation">
        <div class="form-group">
          <label for="edu-institution">Institution *</label>
          <input
            id="edu-institution"
            v-model="formData.institution"
            type="text"
            class="form-control"
            :class="{ 'input-error': formErrors.institution }"
            required
          />
          <span v-if="formErrors.institution" class="error-message">{{
            formErrors.institution
          }}</span>
        </div>

        <div class="form-group">
          <label for="edu-degree">Degree/Certification *</label>
          <input
            id="edu-degree"
            v-model="formData.degree"
            type="text"
            class="form-control"
            :class="{ 'input-error': formErrors.degree }"
            required
          />
          <span v-if="formErrors.degree" class="error-message">{{ formErrors.degree }}</span>
        </div>

        <div class="form-group">
          <label for="edu-field">Field of Study</label>
          <input
            id="edu-field"
            v-model="formData.field_of_study"
            type="text"
            class="form-control"
            :class="{ 'input-error': formErrors.field_of_study }"
          />
          <span v-if="formErrors.field_of_study" class="error-message">{{
            formErrors.field_of_study
          }}</span>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="edu-start-date">Start Date</label>
            <input
              id="edu-start-date"
              v-model="formData.start_date"
              type="date"
              class="form-control"
              :class="{ 'input-error': formErrors.start_date }"
            />
            <span v-if="formErrors.start_date" class="error-message">{{
              formErrors.start_date
            }}</span>
          </div>
          <div class="form-group">
            <label for="edu-end-date">End Date</label>
            <input
              id="edu-end-date"
              v-model="formData.end_date"
              type="date"
              class="form-control"
              :class="{ 'input-error': formErrors.end_date }"
            />
            <span v-if="formErrors.end_date" class="error-message">{{ formErrors.end_date }}</span>
          </div>
        </div>

        <div class="form-group">
          <label for="edu-location">Location</label>
          <input
            id="edu-location"
            v-model="formData.location"
            type="text"
            class="form-control"
            :class="{ 'input-error': formErrors.location }"
          />
          <span v-if="formErrors.location" class="error-message">{{ formErrors.location }}</span>
        </div>

        <div class="form-group">
          <label for="edu-description">Description</label>
          <textarea
            id="edu-description"
            v-model="formData.description"
            class="form-control"
            rows="3"
            :class="{ 'input-error': formErrors.description }"
          ></textarea>
          <span v-if="formErrors.description" class="error-message">{{
            formErrors.description
          }}</span>
        </div>

        <div class="form-check">
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
            v-model.number="formData.order_index"
            type="number"
            class="form-control"
            min="0"
            :class="{ 'input-error': formErrors.order_index }"
          />
          <span v-if="formErrors.order_index" class="error-message">{{
            formErrors.order_index
          }}</span>
        </div>

        <!-- Inline error summary so a failed validation pass is visible even
             without scrolling to the offending field. -->
        <div
          v-if="Object.keys(formErrors).length"
          class="error-summary"
          role="alert"
          aria-live="polite"
        >
          Please fix the highlighted field{{ Object.keys(formErrors).length === 1 ? '' : 's' }}
          before saving.
        </div>

        <div class="form-actions">
          <button
            type="button"
            class="btn-cancel btn-secondary"
            :disabled="isSaving"
            @click="closeForm"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn-save btn-primary"
            :disabled="isSaving"
            :aria-busy="isSaving"
          >
            <span v-if="isSaving">Saving…</span>
            <span v-else>{{ editingEducation ? 'Update' : 'Add' }} Education</span>
          </button>
        </div>
      </form>
    </AdminFormModal>

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
              <td>{{ edu.order_index }}</td>
              <td>
                <button class="btn-row-action btn-row-edit btn-warning" @click="editEducation(edu)">
                  Edit
                </button>
                <button
                  class="btn-row-action btn-row-delete btn-danger"
                  @click="deleteEducation(edu.id)"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-muted">No degrees added yet.</p>

      <h3>Certifications</h3>
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
              <td>{{ cert.order_index }}</td>
              <td>
                <button
                  class="btn-row-action btn-row-edit btn-warning"
                  @click="editEducation(cert)"
                >
                  Edit
                </button>
                <button
                  class="btn-row-action btn-row-delete btn-danger"
                  @click="deleteEducation(cert.id)"
                >
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
import api from '../../api/client'
import { apiLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'
import AdminFormModal from '@/components/admin/AdminFormModal.vue'

const toast = useToast()

// Education form interface (BUGS-03: backend column is order_index, not order)
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
  order_index: number
}

const authStore = useAuthStore()
const router = useRouter()

const showForm = ref<boolean>(false)
const editingEducation = ref<EducationFormData | null>(null)
const educationList = ref<EducationFormData[]>([])
// BUGS-01: re-entrancy guard on Save.
const isSaving = ref<boolean>(false)

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
  order_index: 0
})

// BUGS-02: client-side validation parity with AdminCompanies / AdminProjects.
// We mirror the backend's String(200)/Text limits so the user sees the
// failure inline instead of as a 422 toast after a round-trip.
const formErrors = ref<Record<string, string>>({})

const validateForm = (): boolean => {
  formErrors.value = {}

  if (!formData.value.institution.trim()) {
    formErrors.value.institution = 'Institution is required'
  } else if (formData.value.institution.length > 200) {
    formErrors.value.institution = 'Institution must be 200 characters or less'
  }

  if (!formData.value.degree.trim()) {
    formErrors.value.degree = 'Degree/certification name is required'
  } else if (formData.value.degree.length > 200) {
    formErrors.value.degree = 'Degree must be 200 characters or less'
  }

  if (formData.value.field_of_study && formData.value.field_of_study.length > 200) {
    formErrors.value.field_of_study = 'Field of study must be 200 characters or less'
  }

  if (formData.value.location && formData.value.location.length > 200) {
    formErrors.value.location = 'Location must be 200 characters or less'
  }

  if (formData.value.end_date && formData.value.start_date) {
    const start = new Date(formData.value.start_date)
    const end = new Date(formData.value.end_date)
    if (end < start) {
      formErrors.value.end_date = 'End date must be on or after start date'
    }
  }

  if (formData.value.description && formData.value.description.length > 5000) {
    formErrors.value.description = 'Description must be 5000 characters or less'
  }

  if (formData.value.order_index < 0) {
    formErrors.value.order_index = 'Display order must be 0 or greater'
  }

  return Object.keys(formErrors.value).length === 0
}

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
  if (!validateForm()) {
    return
  }

  if (isSaving.value) return
  isSaving.value = true

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
  } finally {
    isSaving.value = false
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
  showForm.value = false
  editingEducation.value = null
  formErrors.value = {}
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
    order_index: 0
  }
}

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

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

/* Two-column form layout, mirrors AdminCompanies/AdminProjects. */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

.form-control {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--input-text);
}

.form-check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.form-check-input {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

.form-check-label {
  cursor: pointer;
  color: var(--text-primary);
}

/* Modal-action buttons. Same visual vocabulary as AdminCompanies' Save/Cancel,
   tokenised so dark mode swaps via variables.css. */
.btn-save,
.btn-cancel {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
  border: none;
}

.btn-save {
  background: var(--color-primary);
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-cancel {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--color-border);
}

.btn-cancel:hover:not(:disabled) {
  background: var(--color-hover-bg);
  color: var(--text-primary);
}

.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Per-row actions in the degrees/certifications tables. */
.btn-row-action {
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-base);
  font-size: 0.8125rem;
  font-weight: var(--font-weight-medium);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.btn-row-action + .btn-row-action {
  margin-left: 0.5rem;
}

.btn-row-edit {
  background: rgba(245, 158, 11, 0.15);
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.3);
}

.btn-row-edit:hover {
  background: rgba(245, 158, 11, 0.25);
}

.btn-row-delete {
  background: rgba(220, 38, 38, 0.12);
  color: #991b1b;
  border-color: rgba(220, 38, 38, 0.3);
}

.btn-row-delete:hover {
  background: rgba(220, 38, 38, 0.2);
}

[data-theme='dark'] .btn-row-edit {
  background: rgba(245, 158, 11, 0.18);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.35);
}

[data-theme='dark'] .btn-row-delete {
  background: rgba(248, 113, 113, 0.15);
  color: #fca5a5;
  border-color: rgba(248, 113, 113, 0.35);
}

/* BUGS-02 inline validation styling, mirrors AdminCompanies/AdminProjects. */
.input-error {
  border-color: #dc2626 !important;
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.3) !important;
}

.error-message {
  display: block;
  color: #dc2626;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.error-summary {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(220, 38, 38, 0.08);
  border-left: 3px solid #dc2626;
  color: #991b1b;
  font-size: 0.9rem;
}

[data-theme='dark'] .input-error {
  border-color: #f87171 !important;
}

[data-theme='dark'] .error-message {
  color: #f87171;
}

[data-theme='dark'] .error-summary {
  background: rgba(248, 113, 113, 0.12);
  border-left-color: #f87171;
  color: #fca5a5;
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

[data-theme='dark'] .form-group label {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .form-control {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .form-control:focus {
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.4);
}

/* Focus visible states for buttons */
.btn-save:focus-visible,
.btn-cancel:focus-visible,
.btn-row-action:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

[data-theme='dark'] .btn-save:focus-visible,
[data-theme='dark'] .btn-cancel:focus-visible,
[data-theme='dark'] .btn-row-action:focus-visible {
  outline-color: var(--primary-400);
}

.text-muted {
  color: var(--text-tertiary);
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
