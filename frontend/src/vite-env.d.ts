/// <reference types="vite/client" />

// Vue component type definitions
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  const component: DefineComponent<{}, {}, unknown>
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
