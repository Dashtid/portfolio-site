<template>
  <div class="admin-projects">
    <div class="page-header">
      <h2 class="page-title">Manage Projects</h2>
      <button class="add-button" @click="showAddForm = true">
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
        Add Project
      </button>
    </div>

    <div class="projects-grid">
      <div v-if="loading" class="loading-state">Loading projects...</div>

      <div v-else-if="projects.length === 0" class="empty-state">
        <p>No projects added yet.</p>
      </div>

      <div v-else class="project-cards">
        <div v-for="project in projects" :key="project.id" class="project-card">
          <div class="project-header">
            <div class="project-title-block">
              <h3 class="project-name">{{ project.name }}</h3>
              <span v-if="project.featured" class="featured-badge">Featured</span>
            </div>
            <div class="project-actions">
              <button
                class="action-btn edit-btn"
                :aria-label="`Edit ${project.name}`"
                @click="editProject(project)"
              >
                <svg
                  class="icon-sm"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  aria-hidden="true"
                >
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
              <button
                class="action-btn delete-btn"
                :aria-label="`Delete ${project.name}`"
                @click="deleteProject(project.id)"
              >
                <svg
                  class="icon-sm"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  aria-hidden="true"
                >
                  <path
                    d="M3 6h18m-2 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"
                  />
                </svg>
              </button>
            </div>
          </div>

          <p v-if="companyName(project.company_id)" class="project-company">
            {{ companyName(project.company_id) }}
          </p>
          <p v-if="project.description" class="project-description">{{ project.description }}</p>
          <p
            v-if="project.technologies && project.technologies.length"
            class="project-technologies"
          >
            <span v-for="tech in project.technologies" :key="tech" class="tech-pill">{{
              tech
            }}</span>
          </p>
        </div>
      </div>
    </div>

    <div
      v-if="showAddForm || editingProject"
      ref="modalRef"
      class="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="project-modal-title"
      @click.self="closeForm"
      @keydown.escape="closeForm"
    >
      <div class="modal-content">
        <h3 id="project-modal-title" class="modal-title">
          {{ editingProject ? 'Edit Project' : 'Add New Project' }}
        </h3>

        <form class="project-form" @submit.prevent="saveProject">
          <div class="form-group">
            <label for="name">Project Name *</label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              required
              class="form-input"
              :class="{ 'input-error': formErrors.name }"
            />
            <span v-if="formErrors.name" class="error-message">{{ formErrors.name }}</span>
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <textarea
              id="description"
              v-model="form.description"
              rows="3"
              class="form-textarea"
              :class="{ 'input-error': formErrors.description }"
            ></textarea>
            <span v-if="formErrors.description" class="error-message">{{
              formErrors.description
            }}</span>
          </div>

          <div class="form-group">
            <label for="detailed_description">Detailed Description</label>
            <textarea
              id="detailed_description"
              v-model="form.detailed_description"
              rows="6"
              class="form-textarea"
              :class="{ 'input-error': formErrors.detailed_description }"
            ></textarea>
            <span v-if="formErrors.detailed_description" class="error-message">{{
              formErrors.detailed_description
            }}</span>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="github_url">GitHub URL</label>
              <input id="github_url" v-model="form.github_url" type="url" class="form-input" />
            </div>
            <div class="form-group">
              <label for="live_url">Live URL</label>
              <input id="live_url" v-model="form.live_url" type="url" class="form-input" />
            </div>
          </div>

          <div class="form-group">
            <label for="image_url">Image URL</label>
            <input id="image_url" v-model="form.image_url" type="url" class="form-input" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="video_url">Video URL</label>
              <input id="video_url" v-model="form.video_url" type="url" class="form-input" />
            </div>
            <div class="form-group">
              <label for="video_title">Video Title</label>
              <input
                id="video_title"
                v-model="form.video_title"
                type="text"
                class="form-input"
                :class="{ 'input-error': formErrors.video_title }"
              />
              <span v-if="formErrors.video_title" class="error-message">{{
                formErrors.video_title
              }}</span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="map_url">Map URL</label>
              <input id="map_url" v-model="form.map_url" type="url" class="form-input" />
            </div>
            <div class="form-group">
              <label for="map_title">Map Title</label>
              <input
                id="map_title"
                v-model="form.map_title"
                type="text"
                class="form-input"
                :class="{ 'input-error': formErrors.map_title }"
              />
              <span v-if="formErrors.map_title" class="error-message">{{
                formErrors.map_title
              }}</span>
            </div>
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
            <label for="responsibilities">Responsibilities (comma-separated)</label>
            <input
              id="responsibilities"
              v-model="responsibilitiesInput"
              type="text"
              placeholder="Backend design, code review, on-call"
              class="form-input"
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="company_id">Company</label>
              <select id="company_id" v-model="form.company_id" class="form-input">
                <option :value="null">— None —</option>
                <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
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
          </div>

          <div class="form-group form-checkbox">
            <label for="featured">
              <input id="featured" v-model="form.featured" type="checkbox" />
              <span>Featured project</span>
            </label>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="closeForm">Cancel</button>
            <button type="submit" class="btn-save">
              {{ editingProject ? 'Update' : 'Add' }} Project
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, type WritableComputedRef } from 'vue'
import apiClient from '../../api/client'
import type { Company, Project } from '@/types'
import { apiLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'
import { useFocusTrap } from '@/composables/useFocusTrap'

const toast = useToast()

const modalRef = ref<HTMLElement | null>(null)
const { activate: activateFocusTrap, deactivate: deactivateFocusTrap } = useFocusTrap(modalRef)

interface ProjectFormData {
  name: string
  description: string
  detailed_description: string
  technologies: string[]
  responsibilities: string[]
  github_url: string
  live_url: string
  image_url: string
  video_url: string
  video_title: string
  map_url: string
  map_title: string
  company_id: string | null
  featured: boolean
  order_index: number
}

const emptyForm = (): ProjectFormData => ({
  name: '',
  description: '',
  detailed_description: '',
  technologies: [],
  responsibilities: [],
  github_url: '',
  live_url: '',
  image_url: '',
  video_url: '',
  video_title: '',
  map_url: '',
  map_title: '',
  company_id: null,
  featured: false,
  order_index: 0
})

const projects = ref<Project[]>([])
const companies = ref<Company[]>([])
const loading = ref<boolean>(false)
const showAddForm = ref<boolean>(false)
const editingProject = ref<Project | null>(null)

const form = ref<ProjectFormData>(emptyForm())
const formErrors = ref<Record<string, string>>({})

const validateForm = (): boolean => {
  formErrors.value = {}

  if (!form.value.name.trim()) {
    formErrors.value.name = 'Project name is required'
  } else if (form.value.name.length > 200) {
    formErrors.value.name = 'Project name must be 200 characters or less'
  }

  if (form.value.description && form.value.description.length > 1000) {
    formErrors.value.description = 'Description must be 1000 characters or less'
  }

  if (form.value.detailed_description && form.value.detailed_description.length > 10000) {
    formErrors.value.detailed_description = 'Detailed description must be 10000 characters or less'
  }

  if (form.value.video_title && form.value.video_title.length > 200) {
    formErrors.value.video_title = 'Video title must be 200 characters or less'
  }

  if (form.value.map_title && form.value.map_title.length > 200) {
    formErrors.value.map_title = 'Map title must be 200 characters or less'
  }

  return Object.keys(formErrors.value).length === 0
}

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

const responsibilitiesInput: WritableComputedRef<string> = computed({
  get(): string {
    return Array.isArray(form.value.responsibilities) ? form.value.responsibilities.join(', ') : ''
  },
  set(value: string): void {
    form.value.responsibilities = value
      .split(',')
      .map(r => r.trim())
      .filter(r => r)
  }
})

const companyName = (companyId: string | null | undefined): string => {
  if (!companyId) return ''
  return companies.value.find(c => c.id === companyId)?.name ?? ''
}

const fetchAll = async (): Promise<void> => {
  loading.value = true
  try {
    const [projectsResp, companiesResp] = await Promise.all([
      apiClient.get<Project[]>('/api/v1/projects'),
      apiClient.get<Company[]>('/api/v1/companies')
    ])
    projects.value = projectsResp.data
    companies.value = companiesResp.data
  } catch (error) {
    apiLogger.error('Error fetching projects:', error)
    toast.error('Failed to load projects')
  } finally {
    loading.value = false
  }
}

const editProject = (project: Project): void => {
  editingProject.value = project

  // technologies arrives as an array on Project (zod schema enforces it),
  // but we still guard against legacy server responses returning a string.
  let technologies: string[] = []
  if (Array.isArray(project.technologies)) {
    technologies = project.technologies
  } else if (typeof project.technologies === 'string' && project.technologies) {
    technologies = (project.technologies as string)
      .split(',')
      .map(t => t.trim())
      .filter(t => t)
  }

  // responsibilities is typed as string|null on the public schema, but the
  // backend admit-side stores it as a list. Normalise both shapes.
  let responsibilities: string[] = []
  const rawResp = (project as Project & { responsibilities?: string[] | string | null })
    .responsibilities
  if (Array.isArray(rawResp)) {
    responsibilities = rawResp
  } else if (typeof rawResp === 'string' && rawResp) {
    responsibilities = rawResp
      .split(',')
      .map(r => r.trim())
      .filter(r => r)
  }

  form.value = {
    name: project.name,
    description: project.description ?? '',
    detailed_description: project.detailed_description ?? '',
    technologies,
    responsibilities,
    github_url: project.github_url ?? '',
    live_url: project.live_url ?? '',
    image_url: project.image_url ?? '',
    video_url: project.video_url ?? '',
    video_title: project.video_title ?? '',
    map_url: project.map_url ?? '',
    map_title: project.map_title ?? '',
    company_id: project.company_id ?? null,
    featured: !!project.featured,
    order_index: project.order_index ?? 0
  }
}

const saveProject = async (): Promise<void> => {
  if (!validateForm()) {
    return
  }

  // Send empty optional strings as null so the backend doesn't store "" as
  // a value where None is meant. Lists stay as arrays — backend expects them.
  const blankToNull = (s: string): string | null => (s.trim() === '' ? null : s.trim())
  const payload = {
    name: form.value.name.trim(),
    description: blankToNull(form.value.description),
    detailed_description: blankToNull(form.value.detailed_description),
    technologies: form.value.technologies,
    responsibilities: form.value.responsibilities.length ? form.value.responsibilities : null,
    github_url: blankToNull(form.value.github_url),
    live_url: blankToNull(form.value.live_url),
    image_url: blankToNull(form.value.image_url),
    video_url: blankToNull(form.value.video_url),
    video_title: blankToNull(form.value.video_title),
    map_url: blankToNull(form.value.map_url),
    map_title: blankToNull(form.value.map_title),
    company_id: form.value.company_id || null,
    featured: form.value.featured,
    order_index: form.value.order_index
  }

  try {
    if (editingProject.value) {
      await apiClient.put(`/api/v1/projects/${editingProject.value.id}`, payload)
      toast.success('Project updated successfully')
    } else {
      await apiClient.post('/api/v1/projects', payload)
      toast.success('Project added successfully')
    }
    closeForm()
    fetchAll()
  } catch (error) {
    apiLogger.error('Error saving project:', error)
    toast.error('Failed to save project')
  }
}

const deleteProject = async (id: string): Promise<void> => {
  if (!confirm('Are you sure you want to delete this project?')) {
    return
  }
  try {
    await apiClient.delete(`/api/v1/projects/${id}`)
    toast.success('Project deleted successfully')
    fetchAll()
  } catch (error) {
    apiLogger.error('Error deleting project:', error)
    toast.error('Failed to delete project')
  }
}

const closeForm = (): void => {
  deactivateFocusTrap()
  showAddForm.value = false
  editingProject.value = null
  formErrors.value = {}
  form.value = emptyForm()
}

watch(
  () => showAddForm.value || editingProject.value,
  isOpen => {
    if (isOpen) {
      activateFocusTrap()
    }
  }
)

onMounted((): void => {
  fetchAll()
})
</script>

<style scoped>
.admin-projects {
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

.projects-grid {
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

.project-cards {
  display: grid;
  gap: var(--spacing-4);
}

.project-card {
  padding: var(--spacing-4);
  background: var(--color-gray-50);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-200);
  transition: all var(--transition-base) ease;
}

.project-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-2);
  gap: var(--spacing-3);
}

.project-title-block {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.project-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin: 0;
}

.featured-badge {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-primary);
  color: white;
}

.project-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-shrink: 0;
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

.project-company {
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  margin: 0 0 var(--spacing-1);
}

.project-description {
  color: var(--color-gray-700);
  line-height: var(--line-height-relaxed);
  margin: 0 0 var(--spacing-2);
}

.project-technologies {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

.tech-pill {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-gray-200);
  color: var(--color-gray-700);
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
  padding: var(--spacing-4);
}

.modal-content {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  max-width: 720px;
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

.project-form {
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

.form-checkbox label {
  flex-direction: row;
  align-items: center;
  gap: var(--spacing-2);
  cursor: pointer;
}

.form-input,
.form-textarea {
  padding: var(--spacing-2);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: border-color var(--transition-base) ease;
  background: white;
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

.input-error {
  border-color: #dc2626 !important;
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.3) !important;
}

.error-message {
  color: #dc2626;
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-1);
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

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-content {
    padding: var(--spacing-4);
  }
}

[data-theme='dark'] .page-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .projects-grid {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .loading-state,
[data-theme='dark'] .empty-state {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .project-card {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .project-card:hover {
  border-color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .project-name {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .project-company {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .project-description {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .tech-pill {
  background: var(--bg-secondary, #1e293b);
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

[data-theme='dark'] .input-error {
  border-color: #f87171 !important;
}

[data-theme='dark'] .input-error:focus {
  box-shadow: 0 0 0 3px rgba(248, 113, 113, 0.3) !important;
}

[data-theme='dark'] .error-message {
  color: #f87171;
}

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
