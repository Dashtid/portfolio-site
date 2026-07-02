<template>
  <canvas ref="canvasRef" class="hero-canvas" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import {
  Scene,
  PerspectiveCamera,
  WebGLRenderer,
  BufferGeometry,
  BufferAttribute,
  PointsMaterial,
  Points,
  AdditiveBlending,
  NormalBlending,
  type Material
} from 'three'
import { logger } from '../utils/logger'

const props = withDefaults(defineProps<{ isDark?: boolean }>(), { isDark: true })

const canvasRef = ref<HTMLCanvasElement | null>(null)

let scene: Scene
let camera: PerspectiveCamera
let renderer: WebGLRenderer
let particles: Points
let animationId: number
let isReducedMotion = false
let isRunning = false
let inViewport = true
let intersectionObserver: IntersectionObserver | null = null

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
      logger.warn('WebGL not available, skipping Three.js hero background')
      return
    }
  } catch {
    logger.warn('WebGL context check failed, skipping Three.js hero background')
    return
  }

  try {
    // Scene setup
    scene = new Scene()

    // Camera
    camera = new PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.z = 30

    // Renderer with alpha for transparency
    renderer = new WebGLRenderer({
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
    logger.warn('Failed to initialize Three.js:', error)
  }
}

const createParticles = () => {
  const particlesGeometry = new BufferGeometry()

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

    // Particle colors. Dark mode uses a bright cyan-blue gradient designed
    // to glow additively against the near-black hero. Light mode drops
    // brightness and shifts toward a deeper indigo so the dots read as
    // subtle darker points against white (additive blending would just
    // wash out to white; we swap to normal alpha compositing below).
    const colorVariation = Math.random()
    if (props.isDark) {
      colorArray[i3] = 0.2 + colorVariation * 0.2 // R: 0.2-0.4
      colorArray[i3 + 1] = 0.4 + colorVariation * 0.4 // G: 0.4-0.8
      colorArray[i3 + 2] = 0.7 + colorVariation * 0.3 // B: 0.7-1.0
    } else {
      colorArray[i3] = 0.1 + colorVariation * 0.15 // R: 0.10-0.25
      colorArray[i3 + 1] = 0.2 + colorVariation * 0.2 // G: 0.20-0.40
      colorArray[i3 + 2] = 0.5 + colorVariation * 0.4 // B: 0.50-0.90
    }

    // Random sizes for depth effect
    sizeArray[i] = PARTICLE_SIZE * (0.5 + Math.random() * 0.5)
  }

  particlesGeometry.setAttribute('position', new BufferAttribute(posArray, 3))
  particlesGeometry.setAttribute('color', new BufferAttribute(colorArray, 3))
  particlesGeometry.setAttribute('size', new BufferAttribute(sizeArray, 1))

  // Blending mode has to swap per theme:
  //  - AdditiveBlending on dark bg = particles ADD to the (near-black) bg,
  //    producing a bright glow that reads as stars.
  //  - AdditiveBlending on light bg = particles ADD to white, clamped to
  //    white, so they become invisible. NormalBlending alpha-composites
  //    the (darker) particle over white → subtle indigo dots.
  const particlesMaterial = new PointsMaterial({
    size: PARTICLE_SIZE,
    vertexColors: true,
    transparent: true,
    opacity: props.isDark ? 0.6 : 0.7,
    blending: props.isDark ? AdditiveBlending : NormalBlending,
    sizeAttenuation: true,
    depthWrite: false
  })

  particles = new Points(particlesGeometry, particlesMaterial)
  scene.add(particles)
}

const animate = () => {
  // Stop entirely when paused or if renderer wasn't initialized
  if (!renderer || !isRunning) return

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

// The render loop fully stops (no rAF scheduled at all) whenever the
// hero canvas is scrolled out of the viewport or the tab is hidden —
// a full-screen WebGL render at 60fps for an invisible canvas is pure
// battery drain. It restarts when both conditions clear.
const startLoop = () => {
  if (isRunning || !renderer) return
  isRunning = true
  animationId = requestAnimationFrame(animate)
}

const stopLoop = () => {
  isRunning = false
  cancelAnimationFrame(animationId)
}

const updateRunState = () => {
  if (inViewport && !document.hidden) {
    startLoop()
  } else {
    stopLoop()
  }
}

const handleVisibilityChange = () => {
  updateRunState()
}

const handleReducedMotionChange = (event: MediaQueryListEvent) => {
  isReducedMotion = event.matches
}

onMounted(() => {
  // Skip Three.js init if reduced motion is preferred — canvas is also CSS-hidden.
  // The three.js code is in an async chunk via defineAsyncComponent so it doesn't
  // hit the main bundle either way; this just avoids the runtime cost.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    isReducedMotion = true
    return
  }

  initScene()
  startLoop()

  // Event listeners
  window.addEventListener('resize', handleResize, { passive: true })
  window.addEventListener('mousemove', handleMouseMove, { passive: true })
  document.addEventListener('visibilitychange', handleVisibilityChange)

  // Pause rendering while the hero is scrolled out of view
  if (canvasRef.value && 'IntersectionObserver' in window) {
    intersectionObserver = new IntersectionObserver(entries => {
      // Entries are chronological; coalesced leave/enter pairs arrive
      // together, so only the LAST one reflects the current state —
      // reading entries[0] can latch the loop off while visible.
      inViewport = entries[entries.length - 1]?.isIntersecting ?? true
      updateRunState()
    })
    intersectionObserver.observe(canvasRef.value)
  }

  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', handleReducedMotionChange)
})

onBeforeUnmount(() => {
  stopLoop()
  intersectionObserver?.disconnect()

  // Remove event listeners
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('visibilitychange', handleVisibilityChange)

  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.removeEventListener('change', handleReducedMotionChange)

  // Dispose Three.js resources
  if (particles) {
    particles.geometry.dispose()
    ;(particles.material as Material).dispose()
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
