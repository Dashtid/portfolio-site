<template>
  <div class="language-bar">
    <div class="language-info">
      <span class="language-name">{{ name }}</span>
      <span class="language-percentage">{{ percentage }}%</span>
    </div>
    <div
      class="progress-bar"
      role="progressbar"
      :aria-label="`${name} language usage`"
      :aria-valuenow="percentage"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="progress-fill" :style="`width: ${percentage}%`"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  name: string
  percentage: number
}

defineProps<Props>()
</script>

<style scoped>
.language-bar {
  margin-bottom: 1rem;
}

.language-bar:last-child {
  margin-bottom: 0;
}

.language-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.375rem;
  font-size: 0.875rem;
}

.language-name {
  font-weight: 600;
  color: var(--text-secondary);
}

.language-percentage {
  color: var(--text-muted);
  font-weight: 500;
}

.progress-bar {
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500, #3b82f6), var(--primary-600, #2563eb));
  border-radius: 4px;
  transition: width 0.8s ease;
}

/* Dark mode: .language-name (--text-secondary), .progress-bar
   (--color-border), .progress-fill (--primary-500/600) all swap via
   variables.css. Only .language-percentage needs a real override —
   it shifts from --text-muted to --text-tertiary for better dark-mode
   contrast against the bar surface. */
[data-theme='dark'] .language-percentage {
  color: var(--text-tertiary);
}

@media (prefers-reduced-motion: reduce) {
  .progress-fill {
    transition: none;
  }
}
</style>
