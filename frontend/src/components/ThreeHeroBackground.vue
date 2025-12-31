<template>
  <canvas ref="canvasRef" class="hero-canvas" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const canvasRef = ref<HTMLCanvasElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let particles: THREE.Points
let animationId: number
let isReducedMotion = false
let isVisible = true

// Configuration
const PARTICLE_COUNT = 400
const PARTICLE_SIZE = 0.08
const ROTATION_SPEED = 0.0003

// Mouse position tracking
const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 }

const checkReducedMotion = () => {
  isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const initScene = () => {
  if (!canvasRef.value) return

  checkReducedMotion()

  // Check if WebGL is available
  try {
    const testCanvas = document.createElement('canvas')
    const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl')
    if (!gl) {
      console.warn('WebGL not available, skipping Three.js hero background')
      return
    }
  } catch {
    console.warn('WebGL context check failed, skipping Three.js hero background')
    return
  }

  try {
    // Scene setup
    scene = new THREE.Scene()

    // Camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.z = 30

    // Renderer with alpha for transparency
    renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.value,
      alpha: true,
      antialias: true,
      powerPreference: 'low-power' // Optimize for battery life
    })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    // Create particle system
    createParticles()
  } catch (error) {
    console.warn('Failed to initialize Three.js:', error)
  }
}

const createParticles = () => {
  const particlesGeometry = new THREE.BufferGeometry()

  const posArray = new Float32Array(PARTICLE_COUNT * 3)
  const colorArray = new Float32Array(PARTICLE_COUNT * 3)
  const sizeArray = new Float32Array(PARTICLE_COUNT)

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const i3 = i * 3

    // Position - spread particles in a sphere
    const radius = 40 + Math.random() * 20
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)

    posArray[i3] = radius * Math.sin(phi) * Math.cos(theta)
    posArray[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
    posArray[i3 + 2] = (Math.random() - 0.5) * 40

    // Colors - blue to cyan gradient matching portfolio theme
    const colorVariation = Math.random()
    colorArray[i3] = 0.2 + colorVariation * 0.2 // R: 0.2-0.4
    colorArray[i3 + 1] = 0.4 + colorVariation * 0.4 // G: 0.4-0.8
    colorArray[i3 + 2] = 0.7 + colorVariation * 0.3 // B: 0.7-1.0

    // Random sizes for depth effect
    sizeArray[i] = PARTICLE_SIZE * (0.5 + Math.random() * 0.5)
  }

  particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3))
  particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3))
  particlesGeometry.setAttribute('size', new THREE.BufferAttribute(sizeArray, 1))

  // Custom shader material for better particle rendering
  const particlesMaterial = new THREE.PointsMaterial({
    size: PARTICLE_SIZE,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
    depthWrite: false
  })

  particles = new THREE.Points(particlesGeometry, particlesMaterial)
  scene.add(particles)
}

const animate = () => {
  // Skip if renderer wasn't initialized (e.g., WebGL not available)
  if (!renderer) return

  if (!isVisible) {
    animationId = requestAnimationFrame(animate)
    return
  }

  // Smooth mouse following
  mouse.x += (mouse.targetX - mouse.x) * 0.05
  mouse.y += (mouse.targetY - mouse.y) * 0.05

  if (!isReducedMotion && particles) {
    // Gentle continuous rotation
    particles.rotation.y += ROTATION_SPEED
    particles.rotation.x += ROTATION_SPEED * 0.5

    // Mouse-reactive rotation
    particles.rotation.y += mouse.x * 0.001
    particles.rotation.x += mouse.y * 0.001
  }

  renderer.render(scene, camera)
  animationId = requestAnimationFrame(animate)
}

const handleResize = () => {
  // Skip if renderer wasn't initialized
  if (!renderer || !camera) return

  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
}

const handleMouseMove = (event: MouseEvent) => {
  if (isReducedMotion) return

  mouse.targetX = (event.clientX / window.innerWidth) * 2 - 1
  mouse.targetY = -(event.clientY / window.innerHeight) * 2 + 1
}

const handleVisibilityChange = () => {
  isVisible = !document.hidden
}

const handleReducedMotionChange = (event: MediaQueryListEvent) => {
  isReducedMotion = event.matches
}

onMounted(() => {
  initScene()
  animate()

  // Event listeners
  window.addEventListener('resize', handleResize, { passive: true })
  window.addEventListener('mousemove', handleMouseMove, { passive: true })
  document.addEventListener('visibilitychange', handleVisibilityChange)

  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', handleReducedMotionChange)
})

onBeforeUnmount(() => {
  // Cancel animation frame
  cancelAnimationFrame(animationId)

  // Remove event listeners
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('visibilitychange', handleVisibilityChange)

  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.removeEventListener('change', handleReducedMotionChange)

  // Dispose Three.js resources
  if (particles) {
    particles.geometry.dispose()
    ;(particles.material as THREE.Material).dispose()
  }
  renderer?.dispose()
})
</script>

<style scoped>
.hero-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  opacity: 0.7;
}

/* Reduce opacity in dark mode for better contrast */
[data-theme='dark'] .hero-canvas {
  opacity: 0.5;
}

/* Hide on reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .hero-canvas {
    display: none;
  }
}
</style>
