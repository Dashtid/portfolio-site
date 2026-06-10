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
      <h3 :id="titleId" class="modal-title">{{ title }}</h3>
      <slot />
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
  background: white;
  border-radius: var(--radius-lg, 12px);
  padding: var(--spacing-6, 1.5rem);
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
</style>
