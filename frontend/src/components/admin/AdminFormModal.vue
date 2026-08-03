<template>
  <div
    v-if="open"
    ref="modalRef"
    class="modal-overlay"
    role="dialog"
    aria-modal="true"
    :aria-labelledby="titleId"
    @click.self="emit('close')"
    @keydown.escape="emit('close')"
  >
    <div class="modal-content" :style="{ maxWidth }">
      <!-- Header row stays put while .modal-body scrolls: an absolutely
           positioned close button would scroll away with the content on
           forms taller than 90vh, hiding the one visible close affordance
           exactly when the form is long. Escape and click-outside already
           work, but both are invisible — a dialog needs a discoverable,
           focusable close control. The button is the first focusable
           element in the dialog, so the trap lands on it on open (standard
           pattern: AT announces the title via aria-labelledby, then
           "Close dialog, button"). -->
      <div class="modal-header">
        <h3 :id="titleId" class="modal-title">{{ title }}</h3>
        <button class="modal-close" type="button" aria-label="Close dialog" @click="emit('close')">
          &times;
        </button>
      </div>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useFocusTrap } from '@/composables/useFocusTrap'

interface Props {
  open: boolean
  title: string
  titleId?: string
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  titleId: 'admin-modal-title',
  maxWidth: '600px'
})

const emit = defineEmits<{
  close: []
}>()

const modalRef = ref<HTMLElement | null>(null)
const { activate, deactivate } = useFocusTrap(modalRef)

// BUGS-07: previously the watch was lazy, so mounting with `:open="true"`
// (e.g. when a parent restores edit state after navigation) never fired
// activate() and focus escaped the modal. `immediate: true` runs on setup;
// `flush: 'post'` defers until after the DOM update so `modalRef.value` is
// populated by the time activate() reads it.
watch(
  () => props.open,
  isOpen => {
    if (isOpen) {
      activate()
    } else {
      deactivate()
    }
  },
  { immediate: true, flush: 'post' }
)
</script>

<style scoped>
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
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: var(--radius-lg, 12px);
  padding: var(--spacing-6, 1.5rem);
  width: 100%;
  max-height: 90vh;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

/* The BODY scrolls, not .modal-content — that keeps the header (and its
   close button) visible on forms taller than 90vh. */
.modal-body {
  overflow-y: auto;
}

.modal-close {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-base, 8px);
  background: transparent;
  color: var(--color-slate-500, #64748b);
  font-size: var(--font-size-xl);
  line-height: 1;
  cursor: pointer;
}

.modal-close:hover {
  background: var(--color-slate-100, #f1f5f9);
  color: var(--color-slate-900, #0f172a);
}

.modal-close:focus-visible {
  outline: 3px solid var(--primary-400, #60a5fa);
  outline-offset: 2px;
}

.modal-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-slate-900);
  margin: 0; /* spacing owned by .modal-header */
}

@media (max-width: 640px) {
  .modal-content {
    padding: var(--spacing-4);
  }
}

[data-theme='dark'] .modal-overlay {
  background: rgba(0, 0, 0, 0.7);
}

[data-theme='dark'] .modal-content {
  background: var(--bg-secondary, #1e293b);
}

[data-theme='dark'] .modal-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .modal-close {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .modal-close:hover {
  background: var(--color-slate-700, #334155);
  color: var(--text-primary, #f8fafc);
}
</style>
