/// <reference types="vite/client" />

// Vue component type definitions
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Vite environment variables
interface ImportMetaEnv {
  readonly BASE_URL: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
  // Add custom environment variables here
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
