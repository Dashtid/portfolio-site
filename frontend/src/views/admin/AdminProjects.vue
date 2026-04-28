<template>
  <div class="admin-projects">
    <header class="page-header">
      <h2 class="section-title">Projects</h2>
    </header>
    <div class="placeholder-card">
      <svg
        class="placeholder-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        aria-hidden="true"
      >
        <path d="M3 7h18M3 12h18M3 17h12" />
      </svg>
      <h3 class="placeholder-title">Projects management is not wired up yet</h3>
      <p class="placeholder-body">
        Projects on the public site are seeded from the backend; CRUD via this admin view is tracked
        in <code>backlog.md</code>. For now, edit <code>backend/app/seed_data.py</code> and re-run
        seeding.
      </p>
      <router-link to="/admin" class="placeholder-button">Back to dashboard</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
// Intentionally empty — placeholder until project CRUD is implemented.
// See backlog.md "AdminProjects CRUD" for scope.
</script>

<style scoped>
.admin-projects {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0;
}

.placeholder-card {
  background: white;
  border: 1px dashed var(--color-gray-300);
  border-radius: var(--radius-lg);
  padding: var(--spacing-8);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-3);
}

.placeholder-icon {
  width: 40px;
  height: 40px;
  color: var(--color-gray-400);
}

.placeholder-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin: 0;
}

.placeholder-body {
  color: var(--color-gray-600);
  max-width: 540px;
  font-size: var(--font-size-sm);
  line-height: 1.6;
  margin: 0;
}

.placeholder-body code {
  background: var(--color-gray-100);
  padding: 0 0.3em;
  border-radius: 4px;
  font-size: 0.9em;
}

.placeholder-button {
  margin-top: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-primary);
  color: white;
  text-decoration: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: background var(--transition-base) ease;
}

.placeholder-button:hover {
  background: var(--color-primary-700, #1d4ed8);
}

[data-theme='dark'] .section-title,
[data-theme='dark'] .placeholder-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .placeholder-card {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .placeholder-body {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .placeholder-body code {
  background: var(--bg-tertiary, #334155);
}
</style>
