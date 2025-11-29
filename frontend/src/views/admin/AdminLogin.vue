<template>
  <div class="admin-login">
    <div class="login-container">
      <div class="login-card">
        <h1 class="login-title">Admin Login</h1>
        <p class="login-subtitle">Sign in with your GitHub account to manage your portfolio</p>

        <button @click="loginWithGitHub" class="github-login-button">
          <svg class="github-icon" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          <span>Sign in with GitHub</span>
        </button>

        <div class="login-note">
          <p class="note-text">
            Only the authorized admin can sign in to manage portfolio content.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const loginWithGitHub = (): void => {
  authStore.loginWithGitHub()
}
</script>

<style scoped>
.admin-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-teal) 100%);
  padding: var(--spacing-4);
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-card {
  background: white;
  border-radius: var(--radius-xl);
  padding: var(--spacing-8);
  box-shadow: var(--shadow-2xl);
}

.login-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  text-align: center;
  margin: 0 0 var(--spacing-2);
}

.login-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
  text-align: center;
  margin: 0 0 var(--spacing-8);
  line-height: var(--line-height-relaxed);
}

.github-login-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-6);
  background: var(--color-gray-900);
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.github-login-button:hover {
  background: var(--color-gray-800);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.github-icon {
  width: 20px;
  height: 20px;
}

.login-note {
  margin-top: var(--spacing-8);
  padding-top: var(--spacing-6);
  border-top: 1px solid var(--color-gray-200);
}

.note-text {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
  text-align: center;
  margin: 0;
  line-height: var(--line-height-relaxed);
}

/* Mobile Responsive */
@media (max-width: 640px) {
  .login-card {
    padding: var(--spacing-6);
  }

  .login-title {
    font-size: var(--font-size-xl);
  }
}
</style>