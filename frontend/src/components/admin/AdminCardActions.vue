<template>
  <div class="card-actions">
    <button
      class="action-btn edit-btn"
      :aria-label="`Edit ${itemName}`"
      :disabled="deleting"
      @click="emit('edit')"
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
      :aria-label="`Delete ${itemName}`"
      :aria-busy="deleting"
      :disabled="deleting"
      @click="emit('delete')"
    >
      <svg
        class="icon-sm"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        aria-hidden="true"
      >
        <path d="M3 6h18m-2 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  itemName: string
  // BUGS-11: parent passes deletingIds.has(row.id) so a click on the trash
  // icon during a pending DELETE no-ops instead of firing a duplicate.
  deleting?: boolean
}

withDefaults(defineProps<Props>(), { deleting: false })

const emit = defineEmits<{
  edit: []
  delete: []
}>()
</script>

<style scoped>
.card-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-shrink: 0;
}

.action-btn {
  padding: var(--spacing-1);
  background: transparent;
  border: 1px solid var(--color-slate-300);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.action-btn:focus-visible {
  outline: 2px solid var(--color-primary, #2563eb);
  outline-offset: 2px;
}

.edit-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.delete-btn:hover:not(:disabled) {
  /* red-600 literal: Tailwind only emits --color-red-600 while some utility
     happens to use red-600, so var() here would be a coin flip per build. */
  background: #dc2626;
  border-color: #dc2626;
  color: white;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

[data-theme='dark'] .action-btn {
  border-color: var(--border-primary, #475569);
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .action-btn:focus-visible {
  outline-color: var(--primary-400, #60a5fa);
}
</style>
