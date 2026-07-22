<template>
  <div class="admin-cv">
    <!-- Everything except the rendered CV is print:hidden so Ctrl+P / the
         Print button produces just the CV document. -->
    <div class="print:hidden">
      <div class="admin-header">
        <h2>CV Export</h2>
        <div class="header-actions">
          <button
            class="btn-save btn-secondary"
            type="button"
            :disabled="!exportData"
            @click="downloadJson"
          >
            Download JSON
          </button>
          <button
            class="btn-save btn-primary"
            type="button"
            :disabled="!exportData"
            @click="printCv"
          >
            Print / Save as PDF
          </button>
        </div>
      </div>

      <p class="intro">
        The public site is your CV — there is no public CV page. This screen assembles a complete,
        downloadable CV from the data you already maintain:
        <strong>Experience, Education and Skills come straight from their own admin pages</strong>,
        so keeping the site current keeps this CV current. Here you edit the profile prose and your
        private contact (never shown publicly), then print to PDF or download the JSON.
      </p>

      <form v-if="profile" class="cv-form" @submit.prevent="save">
        <fieldset>
          <legend>Identity &amp; headline</legend>
          <div class="form-group">
            <label for="cv-name">Name</label>
            <input id="cv-name" v-model="profile.name" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label for="cv-label">Headline / label</label>
            <input id="cv-label" v-model="profile.label" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label for="cv-summary">Summary</label>
            <textarea
              id="cv-summary"
              v-model="profile.summary"
              class="form-control"
              rows="4"
            ></textarea>
          </div>
          <div class="form-group">
            <label for="cv-focus">Current focus</label>
            <textarea
              id="cv-focus"
              v-model="profile.focus"
              class="form-control"
              rows="2"
            ></textarea>
          </div>
        </fieldset>

        <fieldset>
          <legend>Location &amp; links</legend>
          <div class="form-row">
            <div class="form-group">
              <label for="cv-city">City</label>
              <input
                id="cv-city"
                v-model="profile.location_city"
                type="text"
                class="form-control"
              />
            </div>
            <div class="form-group">
              <label for="cv-region">Region</label>
              <input
                id="cv-region"
                v-model="profile.location_region"
                type="text"
                class="form-control"
              />
            </div>
            <div class="form-group">
              <label for="cv-country">Country code</label>
              <input
                id="cv-country"
                v-model="profile.location_country"
                type="text"
                maxlength="2"
                class="form-control"
              />
            </div>
          </div>
          <div class="form-group">
            <label for="cv-url">Website URL</label>
            <input id="cv-url" v-model="profile.url" type="url" class="form-control" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cv-linkedin">LinkedIn URL</label>
              <input
                id="cv-linkedin"
                v-model="profile.linkedin_url"
                type="url"
                class="form-control"
              />
            </div>
            <div class="form-group">
              <label for="cv-github">GitHub URL</label>
              <input id="cv-github" v-model="profile.github_url" type="url" class="form-control" />
            </div>
          </div>
        </fieldset>

        <fieldset>
          <legend>Private contact</legend>
          <p class="fieldset-note">
            Stored only in the admin-gated database and rendered only on the downloaded CV — never
            on the public site, the API, or the site bundle.
          </p>
          <div class="form-row">
            <div class="form-group">
              <label for="cv-email">Email</label>
              <input id="cv-email" v-model="profile.email" type="email" class="form-control" />
            </div>
            <div class="form-group">
              <label for="cv-phone">Phone</label>
              <input id="cv-phone" v-model="profile.phone" type="tel" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label for="cv-personnummer">Personnummer (optional)</label>
            <input
              id="cv-personnummer"
              v-model="profile.personnummer"
              type="text"
              class="form-control"
              autocomplete="off"
            />
            <span class="field-hint">
              Leave blank unless an employer requires it — modern Swedish CVs omit it, and it is
              needless identity-theft exposure. Blank means it never appears on the CV.
            </span>
          </div>
        </fieldset>

        <fieldset>
          <legend>Languages</legend>
          <div v-for="(lang, index) in profile.languages" :key="index" class="lang-row">
            <input
              v-model="lang.language"
              type="text"
              class="form-control"
              placeholder="Language"
              :aria-label="`Language ${index + 1}`"
            />
            <input
              v-model="lang.fluency"
              type="text"
              class="form-control"
              placeholder="Fluency"
              :aria-label="`Fluency ${index + 1}`"
            />
            <button
              type="button"
              class="btn-row-action btn-row-delete btn-danger"
              @click="removeLanguage(index)"
            >
              Remove
            </button>
          </div>
          <button type="button" class="btn-cancel btn-secondary" @click="addLanguage">
            Add language
          </button>
        </fieldset>

        <div class="form-actions">
          <button
            type="submit"
            class="btn-save btn-primary"
            :disabled="isSaving"
            :aria-busy="isSaving"
          >
            <span v-if="isSaving">Saving…</span>
            <span v-else>Save profile</span>
          </button>
        </div>
      </form>

      <p v-else-if="loadError" class="text-muted">{{ loadError }}</p>
      <p v-else class="text-muted">Loading…</p>

      <h3 v-if="exportData" class="preview-title">Preview</h3>
    </div>

    <!-- The one thing that prints. -->
    <div v-if="exportData" class="cv-preview">
      <CvDocument :resume="exportData" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'
import { apiLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'
import CvDocument from '@/components/cv/CvDocument.vue'
import type { CvProfile, CvResume } from '@/types/cv'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const profile = ref<CvProfile | null>(null)
const exportData = ref<CvResume | null>(null)
const isSaving = ref<boolean>(false)
const loadError = ref<string | null>(null)

const fetchProfile = async (): Promise<void> => {
  const response = await api.get<CvProfile>('/api/v1/admin/cv/profile')
  // Guard against a null languages column from a freshly-created singleton.
  response.data.languages = response.data.languages ?? []
  profile.value = response.data
}

const fetchExport = async (): Promise<void> => {
  const response = await api.get<CvResume>('/api/v1/admin/cv/export')
  exportData.value = response.data
}

const load = async (): Promise<void> => {
  try {
    loadError.value = null
    await Promise.all([fetchProfile(), fetchExport()])
  } catch (error) {
    apiLogger.error('Error loading CV data:', error)
    loadError.value = 'Failed to load CV data.'
    toast.error('Failed to load CV data')
  }
}

const save = async (): Promise<void> => {
  if (!profile.value || isSaving.value) return
  isSaving.value = true
  try {
    const p = profile.value
    await api.put('/api/v1/admin/cv/profile', {
      name: p.name,
      label: p.label,
      summary: p.summary,
      focus: p.focus,
      location_city: p.location_city,
      location_region: p.location_region,
      location_country: p.location_country,
      url: p.url,
      linkedin_url: p.linkedin_url,
      github_url: p.github_url,
      // Prune blank/whitespace rows: the backend requires a non-empty
      // language name (min_length=1), so an unfilled "Add language" row
      // would 422 the whole PUT and silently drop every other edit.
      languages: p.languages
        .map(l => ({ language: l.language.trim(), fluency: l.fluency.trim() }))
        .filter(l => l.language.length > 0),
      email: p.email,
      phone: p.phone,
      personnummer: p.personnummer
    })
    toast.success('CV profile saved')
    // Re-assemble the export so the preview reflects the saved profile.
    await fetchExport()
  } catch (error) {
    apiLogger.error('Error saving CV profile:', error)
    toast.error('Failed to save CV profile')
  } finally {
    isSaving.value = false
  }
}

const addLanguage = (): void => {
  profile.value?.languages.push({ language: '', fluency: '' })
}

const removeLanguage = (index: number): void => {
  profile.value?.languages.splice(index, 1)
}

const printCv = (): void => {
  window.print()
}

const slugify = (value: string): string =>
  value
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'cv'

const downloadJson = (): void => {
  if (!exportData.value) return
  const blob = new Blob([JSON.stringify(exportData.value, null, 2)], {
    type: 'application/json'
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${slugify(exportData.value.basics.name)}-cv.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(async (): Promise<void> => {
  if (!authStore.isAuthenticated) {
    router.push('/admin/login')
    return
  }
  await load()
})
</script>

<style scoped>
.admin-cv {
  padding: 2rem;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.intro {
  max-width: 60ch;
  margin-bottom: 2rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.cv-form fieldset {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1.25rem 1.25rem 0.75rem;
  margin-bottom: 1.5rem;
}

.cv-form legend {
  padding: 0 0.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.fieldset-note {
  margin: -0.25rem 0 1rem;
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-row:has(#cv-country) {
  grid-template-columns: 2fr 2fr 1fr;
}

@media (max-width: 640px) {
  .form-row,
  .form-row:has(#cv-country) {
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

.field-hint {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.lang-row {
  display: grid;
  grid-template-columns: 2fr 2fr auto;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  align-items: center;
}

.btn-save,
.btn-cancel {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
  border: none;
}

.btn-save.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-save.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.btn-save.btn-secondary,
.btn-cancel.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--color-border);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-row-action {
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-base);
  font-size: 0.8125rem;
  font-weight: var(--font-weight-medium);
  border: 1px solid transparent;
  cursor: pointer;
}

.btn-row-delete {
  background: rgba(220, 38, 38, 0.12);
  color: #991b1b;
  border-color: rgba(220, 38, 38, 0.3);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.preview-title {
  margin: 2rem 0 1rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.cv-preview {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.text-muted {
  color: var(--text-tertiary);
}

.btn-save:focus-visible,
.btn-cancel:focus-visible,
.btn-row-action:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

@media print {
  .admin-cv {
    padding: 0;
  }

  .cv-preview {
    border: none;
    border-radius: 0;
  }
}

[data-theme='dark'] .admin-cv h2,
[data-theme='dark'] .admin-cv h3 {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .form-group label,
[data-theme='dark'] .cv-form legend {
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

[data-theme='dark'] .cv-form fieldset {
  border-color: var(--border-primary, #475569);
}
</style>
