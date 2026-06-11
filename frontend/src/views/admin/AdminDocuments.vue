<template>
  <div class="admin-documents">
    <div class="page-header">
      <h2 class="page-title">Manage Documents</h2>
      <button class="add-button" @click="openCreateForm">
        <svg
          class="icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <path d="M12 4v16m8-8H4" />
        </svg>
        Add Document
      </button>
    </div>

    <div class="documents-grid">
      <div v-if="loading" class="loading-state">Loading documents…</div>

      <div v-else-if="docs.length === 0" class="empty-state">
        <p>No documents added yet.</p>
      </div>

      <div v-else class="doc-table-wrap">
        <table class="doc-table">
          <thead>
            <tr>
              <th scope="col">Title</th>
              <th scope="col">Type</th>
              <th scope="col">Size</th>
              <th scope="col">Published</th>
              <th scope="col">Order</th>
              <th scope="col" class="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in docs" :key="doc.id">
              <td>{{ doc.title }}</td>
              <td>{{ doc.document_type }}</td>
              <td>{{ formatFileSize(doc.file_size) }}</td>
              <td>{{ doc.published_date || '—' }}</td>
              <td>{{ doc.order_index }}</td>
              <td>
                <AdminCardActions
                  :item-name="doc.title"
                  :deleting="deletingIds.has(doc.id)"
                  @edit="editDoc(doc)"
                  @delete="deleteDoc(doc.id)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminFormModal
      :open="showForm"
      :title="editingDoc ? 'Edit Document' : 'Add New Document'"
      title-id="doc-modal-title"
      @close="closeForm"
    >
      <form class="doc-form" @submit.prevent="saveDoc">
        <div class="form-group">
          <label for="doc-title">Title *</label>
          <input
            id="doc-title"
            v-model="form.title"
            type="text"
            required
            maxlength="200"
            class="form-input"
            :class="{ 'input-error': formErrors.title }"
          />
          <span v-if="formErrors.title" class="error-message">{{ formErrors.title }}</span>
        </div>

        <div class="form-group">
          <label for="doc-description">Description</label>
          <textarea
            id="doc-description"
            v-model="form.description"
            rows="3"
            maxlength="2000"
            class="form-textarea"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="doc-type">Type *</label>
            <select id="doc-type" v-model="form.document_type" required class="form-input">
              <option value="">— Choose —</option>
              <option value="thesis">Thesis</option>
              <option value="paper">Paper</option>
              <option value="report">Report</option>
              <option value="presentation">Presentation</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="form-group">
            <label for="doc-published">Published Date</label>
            <input
              id="doc-published"
              v-model="form.published_date"
              type="date"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label>PDF File *</label>
          <!-- The upload happens BEFORE the row is created. On success
               the form's file_url / file_path / file_size fields are
               populated from the server response, which the row then
               references. Editing an existing doc keeps the previous
               file unless the admin uploads a new one. -->
          <div class="upload-row">
            <input
              ref="fileInput"
              type="file"
              accept="application/pdf"
              :disabled="isUploading"
              class="form-input file-input"
              @change="handleFileSelect"
            />
            <span v-if="isUploading" class="upload-status">Uploading…</span>
            <span v-else-if="form.file_url" class="upload-status upload-status-ok">
              {{ form.file_path ? form.file_path.split('/').pop() : 'File ready' }} ({{
                formatFileSize(form.file_size)
              }})
            </span>
            <span v-else class="upload-hint">Max 25 MB. PDF only.</span>
          </div>
          <span v-if="formErrors.file_url" class="error-message">{{ formErrors.file_url }}</span>
        </div>

        <div class="form-group">
          <label for="doc-order">Display Order</label>
          <input
            id="doc-order"
            v-model.number="form.order_index"
            type="number"
            min="0"
            class="form-input"
          />
        </div>

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
          <button type="button" class="btn-cancel" :disabled="isSaving" @click="closeForm">
            Cancel
          </button>
          <button
            type="submit"
            class="btn-save"
            :disabled="isSaving || isUploading"
            :aria-busy="isSaving"
          >
            <span v-if="isSaving">Saving…</span>
            <span v-else>{{ editingDoc ? 'Update' : 'Add' }} Document</span>
          </button>
        </div>
      </form>
    </AdminFormModal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import apiClient from '../../api/client'
import { adminLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'
import AdminFormModal from '@/components/admin/AdminFormModal.vue'
import AdminCardActions from '@/components/admin/AdminCardActions.vue'

interface Document {
  id: string
  title: string
  description: string | null
  document_type: string
  file_path: string
  file_size: number
  file_url: string
  published_date: string | null
  order_index: number
}

interface DocumentFormData {
  id: string
  title: string
  description: string
  document_type: string
  file_path: string
  file_size: number
  file_url: string
  published_date: string
  order_index: number
}

interface UploadResponse {
  file_path: string
  file_size: number
  file_url: string
  original_filename: string
}

const toast = useToast()

const docs = ref<Document[]>([])
const loading = ref(true)
const showForm = ref(false)
const editingDoc = ref<Document | null>(null)
const isSaving = ref(false)
const isUploading = ref(false)
const deletingIds = ref(new Set<string>())
const fileInput = ref<HTMLInputElement | null>(null)
const formErrors = ref<Record<string, string>>({})

const emptyForm = (): DocumentFormData => ({
  id: '',
  title: '',
  description: '',
  document_type: '',
  file_path: '',
  file_size: 0,
  file_url: '',
  published_date: '',
  order_index: 0
})

const form = ref<DocumentFormData>(emptyForm())

const formatFileSize = (bytes: number): string => {
  if (!bytes) return '—'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

const fetchDocuments = async (): Promise<void> => {
  loading.value = true
  try {
    const response = await apiClient.get<Document[]>('/api/v1/documents/')
    docs.value = response.data
  } catch (error) {
    adminLogger.error('Failed to load documents:', error)
    toast.error('Failed to load documents.')
  } finally {
    loading.value = false
  }
}

const generateId = (): string => {
  // Native UUID where available; falls back to a stable random hex for
  // older browsers that the project still supports.
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}

const openCreateForm = (): void => {
  editingDoc.value = null
  form.value = emptyForm()
  formErrors.value = {}
  showForm.value = true
}

const editDoc = (doc: Document): void => {
  editingDoc.value = doc
  form.value = {
    id: doc.id,
    title: doc.title,
    description: doc.description ?? '',
    document_type: doc.document_type,
    file_path: doc.file_path,
    file_size: doc.file_size,
    file_url: doc.file_url,
    published_date: doc.published_date ?? '',
    order_index: doc.order_index
  }
  formErrors.value = {}
  showForm.value = true
}

const closeForm = (): void => {
  if (isSaving.value || isUploading.value) return
  showForm.value = false
  editingDoc.value = null
  form.value = emptyForm()
  formErrors.value = {}
  if (fileInput.value) fileInput.value.value = ''
}

const handleFileSelect = async (event: Event): Promise<void> => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (file.type !== 'application/pdf') {
    formErrors.value.file_url = 'PDF files only.'
    target.value = ''
    return
  }
  if (file.size > 25 * 1024 * 1024) {
    formErrors.value.file_url = 'File exceeds 25 MB limit.'
    target.value = ''
    return
  }

  isUploading.value = true
  formErrors.value.file_url = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<UploadResponse>('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    form.value.file_path = response.data.file_path
    form.value.file_size = response.data.file_size
    form.value.file_url = response.data.file_url
    toast.success('File uploaded.')
  } catch (error) {
    adminLogger.error('Upload failed:', error)
    formErrors.value.file_url = 'Upload failed. Try again.'
    toast.error('Upload failed.')
  } finally {
    isUploading.value = false
  }
}

const validateForm = (): boolean => {
  const errors: Record<string, string> = {}
  if (!form.value.title.trim()) errors.title = 'Title is required.'
  else if (form.value.title.length > 200) errors.title = 'Title is too long (max 200).'
  if (!form.value.document_type) errors.document_type = 'Type is required.'
  if (!form.value.file_url) errors.file_url = 'Upload a file first.'
  formErrors.value = errors
  return Object.keys(errors).length === 0
}

const saveDoc = async (): Promise<void> => {
  if (!validateForm()) return
  if (isSaving.value) return
  isSaving.value = true

  try {
    if (editingDoc.value) {
      await apiClient.put(`/api/v1/documents/${editingDoc.value.id}`, {
        title: form.value.title,
        description: form.value.description || null,
        document_type: form.value.document_type,
        file_path: form.value.file_path,
        file_size: form.value.file_size,
        file_url: form.value.file_url,
        published_date: form.value.published_date || null,
        order_index: form.value.order_index
      })
      toast.success('Document updated.')
    } else {
      await apiClient.post('/api/v1/documents/', {
        id: form.value.id || generateId(),
        title: form.value.title,
        description: form.value.description || null,
        document_type: form.value.document_type,
        file_path: form.value.file_path,
        file_size: form.value.file_size,
        file_url: form.value.file_url,
        published_date: form.value.published_date || null,
        order_index: form.value.order_index
      })
      toast.success('Document added.')
    }
    showForm.value = false
    editingDoc.value = null
    form.value = emptyForm()
    await fetchDocuments()
  } catch (error) {
    adminLogger.error('Save failed:', error)
    toast.error('Save failed.')
  } finally {
    isSaving.value = false
  }
}

const deleteDoc = async (id: string): Promise<void> => {
  if (deletingIds.value.has(id)) return
  if (!window.confirm('Delete this document? This cannot be undone.')) return
  deletingIds.value.add(id)
  try {
    await apiClient.delete(`/api/v1/documents/${id}`)
    toast.success('Document deleted.')
    await fetchDocuments()
  } catch (error) {
    adminLogger.error('Delete failed:', error)
    toast.error('Delete failed.')
  } finally {
    deletingIds.value.delete(id)
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.admin-documents {
  padding: var(--spacing-4) 0;
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
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
}

.icon {
  width: 18px;
  height: 18px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-gray-600);
  background: white;
  border: 1px dashed var(--color-gray-300);
  border-radius: var(--radius-lg);
}

.doc-table-wrap {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

.doc-table {
  width: 100%;
  border-collapse: collapse;
}

.doc-table thead {
  background: var(--color-gray-50);
}

.doc-table th,
.doc-table td {
  text-align: left;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-gray-200);
  font-size: var(--font-size-sm);
}

.doc-table tbody tr:last-child td {
  border-bottom: none;
}

.actions-col {
  width: 1%;
  white-space: nowrap;
}

.doc-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.form-input,
.form-textarea {
  padding: var(--spacing-2) var(--spacing-3);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
}

.form-textarea {
  resize: vertical;
}

.input-error {
  border-color: #dc2626;
}

.error-message {
  font-size: var(--font-size-xs);
  color: #dc2626;
}

.error-summary {
  padding: var(--spacing-3);
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-base);
  color: #991b1b;
  font-size: var(--font-size-sm);
}

.upload-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  flex-wrap: wrap;
}

.file-input {
  flex: 1 1 auto;
}

.upload-status {
  font-size: var(--font-size-sm);
  color: var(--color-gray-700);
}

.upload-status-ok {
  color: #047857;
}

.upload-hint {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}

.btn-cancel,
.btn-save {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  border: 1px solid var(--color-gray-300);
}

.btn-cancel {
  background: white;
  color: var(--color-gray-700);
}

.btn-save {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.btn-save:disabled,
.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
