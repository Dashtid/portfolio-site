<template>
  <div class="admin-skills">
    <div class="page-header">
      <h2 class="page-title">Manage Skills</h2>
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
        Add Skill
      </button>
    </div>

    <div class="skills-grid">
      <div v-if="loading" class="loading-state">Loading skills…</div>

      <div v-else-if="skills.length === 0" class="empty-state">
        <p>No skills added yet.</p>
      </div>

      <div v-else class="skill-table-wrap">
        <table class="skill-table">
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Category</th>
              <th scope="col">Proficiency</th>
              <th scope="col">Years</th>
              <th scope="col">Order</th>
              <th scope="col" class="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="skill in skills" :key="skill.id">
              <td class="skill-name-cell">{{ skill.name }}</td>
              <td>{{ skill.category || '—' }}</td>
              <td>
                <div class="proficiency-bar" :aria-label="`${skill.proficiency_level}%`">
                  <div
                    class="proficiency-fill"
                    :style="{ width: `${Math.min(100, Math.max(0, skill.proficiency_level))}%` }"
                  ></div>
                </div>
                <span class="proficiency-label">{{ skill.proficiency_level }}%</span>
              </td>
              <td>{{ skill.years_of_experience ?? '—' }}</td>
              <td>{{ (skill as Skill & { order_index?: number }).order_index ?? 0 }}</td>
              <td>
                <AdminCardActions
                  :item-name="skill.name"
                  @edit="editSkill(skill)"
                  @delete="deleteSkill(skill.id)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminFormModal
      :open="showAddForm || !!editingSkill"
      :title="editingSkill ? 'Edit Skill' : 'Add New Skill'"
      title-id="skill-modal-title"
      @close="closeForm"
    >
      <form class="skill-form" @submit.prevent="saveSkill">
        <div class="form-group">
          <label for="skill-name">Skill Name *</label>
          <input
            id="skill-name"
            v-model="form.name"
            type="text"
            required
            class="form-input"
            :class="{ 'input-error': formErrors.name }"
          />
          <span v-if="formErrors.name" class="error-message">{{ formErrors.name }}</span>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="skill-category">Category</label>
            <select id="skill-category" v-model="form.category" class="form-input">
              <option value="">— Choose —</option>
              <option v-for="opt in CATEGORY_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="skill-years">Years of Experience</label>
            <input
              id="skill-years"
              v-model.number="form.years_of_experience"
              type="number"
              min="0"
              step="0.5"
              class="form-input"
              :class="{ 'input-error': formErrors.years_of_experience }"
            />
            <span v-if="formErrors.years_of_experience" class="error-message">{{
              formErrors.years_of_experience
            }}</span>
          </div>
        </div>

        <div class="form-group">
          <label for="skill-proficiency">
            Proficiency: <strong>{{ form.proficiency_level }}%</strong>
          </label>
          <input
            id="skill-proficiency"
            v-model.number="form.proficiency_level"
            type="range"
            min="0"
            max="100"
            step="5"
            class="form-range"
          />
        </div>

        <div class="form-group">
          <label for="skill-order">Display Order</label>
          <input
            id="skill-order"
            v-model.number="form.order_index"
            type="number"
            min="0"
            class="form-input"
            :class="{ 'input-error': formErrors.order_index }"
          />
          <span v-if="formErrors.order_index" class="error-message">{{
            formErrors.order_index
          }}</span>
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
          <button type="submit" class="btn-save" :disabled="isSaving" :aria-busy="isSaving">
            <span v-if="isSaving">Saving…</span>
            <span v-else>{{ editingSkill ? 'Update' : 'Add' }} Skill</span>
          </button>
        </div>
      </form>
    </AdminFormModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../../api/client'
import type { Skill } from '@/types'
import { apiLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'
import AdminFormModal from '@/components/admin/AdminFormModal.vue'
import AdminCardActions from '@/components/admin/AdminCardActions.vue'

const toast = useToast()

// Curated category list. Free-text would let the admin drift from the
// taxonomy the public site groups by; a dropdown keeps Skill.category
// values consistent across the data set.
const CATEGORY_OPTIONS = [
  'Language',
  'Framework',
  'Tool',
  'Database',
  'Cloud',
  'Security',
  'DevOps',
  'Other'
] as const

interface SkillFormData {
  name: string
  category: string
  proficiency_level: number
  years_of_experience: number | null
  order_index: number
}

const emptyForm = (): SkillFormData => ({
  name: '',
  category: '',
  proficiency_level: 50,
  years_of_experience: null,
  order_index: 0
})

const skills = ref<Skill[]>([])
const loading = ref<boolean>(false)
const isSaving = ref<boolean>(false)
const showAddForm = ref<boolean>(false)
const editingSkill = ref<Skill | null>(null)

const form = ref<SkillFormData>(emptyForm())
const formErrors = ref<Record<string, string>>({})

const validateForm = (): boolean => {
  formErrors.value = {}

  if (!form.value.name.trim()) {
    formErrors.value.name = 'Skill name is required'
  } else if (form.value.name.length > 100) {
    formErrors.value.name = 'Skill name must be 100 characters or less'
  }

  if (form.value.proficiency_level < 0 || form.value.proficiency_level > 100) {
    formErrors.value.proficiency_level = 'Proficiency must be between 0 and 100'
  }

  if (
    form.value.years_of_experience !== null &&
    form.value.years_of_experience !== undefined &&
    form.value.years_of_experience < 0
  ) {
    formErrors.value.years_of_experience = 'Years of experience cannot be negative'
  }

  if (form.value.order_index < 0) {
    formErrors.value.order_index = 'Display order must be 0 or greater'
  }

  return Object.keys(formErrors.value).length === 0
}

const fetchSkills = async (): Promise<void> => {
  loading.value = true
  try {
    const response = await apiClient.get<Skill[]>('/api/v1/skills')
    skills.value = response.data
  } catch (error) {
    apiLogger.error('Error fetching skills:', error)
    toast.error('Failed to load skills')
  } finally {
    loading.value = false
  }
}

const editSkill = (skill: Skill): void => {
  editingSkill.value = skill
  form.value = {
    name: skill.name,
    category: skill.category ?? '',
    proficiency_level: skill.proficiency_level,
    years_of_experience: skill.years_of_experience ?? null,
    order_index: (skill as Skill & { order_index?: number }).order_index ?? 0
  }
}

const saveSkill = async (): Promise<void> => {
  if (!validateForm()) return

  // BUGS-01: re-entrancy guard so a double-click / mashed Enter can't fire
  // two POSTs back to back. The submit button is also disabled while
  // isSaving so this is belt-and-braces.
  if (isSaving.value) return
  isSaving.value = true

  const payload = {
    name: form.value.name.trim(),
    category: form.value.category || null,
    proficiency_level: form.value.proficiency_level,
    years_of_experience: form.value.years_of_experience,
    order_index: form.value.order_index
  }

  try {
    if (editingSkill.value) {
      await apiClient.put(`/api/v1/skills/${editingSkill.value.id}`, payload)
      toast.success('Skill updated successfully')
    } else {
      await apiClient.post('/api/v1/skills', payload)
      toast.success('Skill added successfully')
    }
    closeForm()
    await fetchSkills()
  } catch (error) {
    apiLogger.error('Error saving skill:', error)
    toast.error('Failed to save skill')
  } finally {
    isSaving.value = false
  }
}

const deleteSkill = async (id: string): Promise<void> => {
  if (!confirm('Are you sure you want to delete this skill?')) return
  try {
    await apiClient.delete(`/api/v1/skills/${id}`)
    toast.success('Skill deleted successfully')
    await fetchSkills()
  } catch (error) {
    apiLogger.error('Error deleting skill:', error)
    toast.error('Failed to delete skill')
  }
}

const closeForm = (): void => {
  showAddForm.value = false
  editingSkill.value = null
  formErrors.value = {}
  form.value = emptyForm()
}

onMounted(fetchSkills)
</script>

<style scoped>
.admin-skills {
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

.skills-grid {
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

.skill-table-wrap {
  overflow-x: auto;
}

.skill-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.skill-table th,
.skill-table td {
  text-align: left;
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--color-gray-200);
  vertical-align: middle;
}

.skill-table th {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-700);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: var(--font-size-xs);
}

.skill-name-cell {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
}

.proficiency-bar {
  display: inline-block;
  width: 120px;
  height: 8px;
  background: var(--color-gray-200);
  border-radius: var(--radius-full);
  vertical-align: middle;
  margin-right: var(--spacing-2);
  overflow: hidden;
}

.proficiency-fill {
  height: 100%;
  background: var(--color-primary);
}

.proficiency-label {
  font-variant-numeric: tabular-nums;
  font-size: var(--font-size-xs);
  color: var(--color-gray-600);
}

.actions-col {
  width: 110px;
}

.skill-form {
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

.form-input {
  padding: var(--spacing-2);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: border-color var(--transition-base) ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb, 37, 99, 235), 0.3);
}

.form-range {
  width: 100%;
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

.error-summary {
  padding: var(--spacing-2) var(--spacing-3);
  background: rgba(220, 38, 38, 0.08);
  border-left: 3px solid #dc2626;
  color: #991b1b;
  font-size: var(--font-size-sm);
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

.btn-cancel:hover:not(:disabled) {
  background: var(--color-gray-100);
}

.btn-save {
  background: var(--color-primary);
  color: white;
  border: none;
}

.btn-save:hover:not(:disabled) {
  background: var(--color-primary-dark, #1e40af);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-cancel:disabled,
.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

[data-theme='dark'] .page-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .skills-grid {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .skill-table th {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .skill-table th,
[data-theme='dark'] .skill-table td {
  border-bottom-color: var(--border-primary, #334155);
}

[data-theme='dark'] .skill-name-cell {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .proficiency-bar {
  background: var(--bg-tertiary, #334155);
}

[data-theme='dark'] .proficiency-fill {
  background: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .proficiency-label,
[data-theme='dark'] .loading-state,
[data-theme='dark'] .empty-state {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .form-input {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .form-input:focus {
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.4);
}

[data-theme='dark'] .form-actions {
  border-top-color: var(--border-primary, #475569);
}

[data-theme='dark'] .btn-cancel {
  color: var(--text-secondary, #cbd5e1);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .btn-cancel:hover:not(:disabled) {
  background: var(--bg-tertiary, #334155);
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
</style>
