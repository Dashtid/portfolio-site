<template>
  <canvas ref="canvasRef" class="hero-field" aria-hidden="true" data-testid="hero-field"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

/**
 * D3-DSN-03: Canvas2D "signal field" — the dark-mode hero backdrop that
 * replaced the three.js starfield (122KB gzip rendering pixels a scan
 * showed were below perceptual threshold). ~2KB, no dependencies.
 *
 * A fixed-seed PRNG lays out the same constellation on every load: the
 * field is part of the identity, not random noise — and the dark hero
 * baseline stays deterministic (the three.js version burned the visual
 * diff budget absorbing unseeded Math.random() star placement).
 *
 * Density biases toward the top-right so the left column stays quiet
 * under the headline. Points drift slowly; near neighbors are joined by
 * faint lines so the field reads in a STATIC screenshot — the hard
 * acceptance test the starfield failed. Reduced motion: one static
 * frame at t=0, no animation loop.
 */

const canvasRef = ref<HTMLCanvasElement | null>(null)

const POINT_COUNT = 130
const LINK_DIST = 110
const SEED = 0x5eed_2f88 // constant: same field every visit

interface FieldPoint {
  x: number // 0..1 of width
  y: number // 0..1 of height
  r: number
  alpha: number
  vx: number
  vy: number
  phase: number
}

let ctx: CanvasRenderingContext2D | null = null
let points: FieldPoint[] = []
let rafId = 0
let running = false
let inViewport = true
let reducedMotion = false
let resizeObserver: ResizeObserver | null = null
let intersectionObserver: IntersectionObserver | null = null

// mulberry32 — tiny deterministic PRNG
const mulberry32 = (seed: number) => {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const buildField = (): void => {
  const rand = mulberry32(SEED)
  points = []
  for (let i = 0; i < POINT_COUNT; i++) {
    // Bias x and y toward the top-right: squaring a uniform sample skews
    // it low, so 1-u^2 skews high (right/top after the y flip below).
    const bx = 1 - rand() ** 2
    const by = rand() ** 1.5
    points.push({
      x: bx,
      y: by,
      r: 0.6 + rand() * 1.4,
      alpha: 0.25 + rand() * 0.55,
      vx: (rand() - 0.5) * 0.008,
      vy: (rand() - 0.5) * 0.008,
      phase: rand() * Math.PI * 2
    })
  }
}

const draw = (t: number): void => {
  const canvas = canvasRef.value
  if (!canvas || !ctx) return
  const w = canvas.clientWidth
  const h = canvas.clientHeight
  ctx.clearRect(0, 0, w, h)

  const time = t / 1000

  // Positions in CSS pixels for this frame (drift is a gentle orbit so
  // points never wander out of their seeded neighborhood).
  const px: number[] = []
  const py: number[] = []
  for (let i = 0; i < points.length; i++) {
    const p = points[i]
    const driftX = reducedMotion ? 0 : Math.sin(time * 0.12 + p.phase) * 6
    const driftY = reducedMotion ? 0 : Math.cos(time * 0.1 + p.phase) * 6
    px[i] = p.x * w + driftX
    py[i] = p.y * h + driftY
  }

  // Faint links between near neighbors — the structure that makes the
  // field legible in a still image.
  ctx.lineWidth = 1
  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      const dx = px[i] - px[j]
      const dy = py[i] - py[j]
      const d2 = dx * dx + dy * dy
      if (d2 > LINK_DIST * LINK_DIST) continue
      const a = (1 - Math.sqrt(d2) / LINK_DIST) * 0.16
      ctx.strokeStyle = `rgba(90, 167, 242, ${a.toFixed(3)})`
      ctx.beginPath()
      ctx.moveTo(px[i], py[i])
      ctx.lineTo(px[j], py[j])
      ctx.stroke()
    }
  }

  // Points, with a slow twinkle in motion mode
  for (let i = 0; i < points.length; i++) {
    const p = points[i]
    const twinkle = reducedMotion ? 1 : 0.75 + 0.25 * Math.sin(time * 0.6 + p.phase * 3)
    ctx.fillStyle = `rgba(147, 199, 249, ${(p.alpha * twinkle).toFixed(3)})`
    ctx.beginPath()
    ctx.arc(px[i], py[i], p.r, 0, Math.PI * 2)
    ctx.fill()
  }
}

const frame = (t: number): void => {
  if (!running) return
  draw(t)
  rafId = requestAnimationFrame(frame)
}

const startLoop = (): void => {
  if (running || reducedMotion) return
  running = true
  rafId = requestAnimationFrame(frame)
}

const stopLoop = (): void => {
  running = false
  cancelAnimationFrame(rafId)
}

const updateRunState = (): void => {
  if (inViewport && !document.hidden) startLoop()
  else stopLoop()
}

const resize = (): void => {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = Math.round(canvas.clientWidth * dpr)
  canvas.height = Math.round(canvas.clientHeight * dpr)
  ctx = canvas.getContext('2d')
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  // Repaint immediately so a resize (or the reduced-motion static frame)
  // never leaves a blank canvas.
  draw(0)
}

const handleVisibilityChange = (): void => updateRunState()

onMounted(() => {
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  buildField()
  resize()

  if ('ResizeObserver' in window && canvasRef.value) {
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(canvasRef.value)
  } else {
    window.addEventListener('resize', resize, { passive: true })
  }

  if (!reducedMotion) {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    if (canvasRef.value && 'IntersectionObserver' in window) {
      intersectionObserver = new IntersectionObserver(entries => {
        inViewport = entries[entries.length - 1]?.isIntersecting ?? true
        updateRunState()
      })
      intersectionObserver.observe(canvasRef.value)
    }
    startLoop()
  }
})

onBeforeUnmount(() => {
  stopLoop()
  resizeObserver?.disconnect()
  intersectionObserver?.disconnect()
  window.removeEventListener('resize', resize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.hero-field {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}
</style>
