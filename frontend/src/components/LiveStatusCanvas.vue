<template>
  <!-- Official LiveStatusLoading: lottie-web canvas, speed=2, size default 16 -->
  <div
    ref="containerRef"
    :class="className"
    :style="{ width: `${size}px`, height: `${size}px` }"
  />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import lottie, { type AnimationItem } from 'lottie-web'
import animationData from '@/assets/live-status-loading.json'

const props = withDefaults(
  defineProps<{
    size?: number
    className?: string
    /** Pause animation when false (e.g. completed step swaps away). */
    active?: boolean
  }>(),
  { size: 16, className: undefined, active: true },
)

const containerRef = ref<HTMLDivElement | null>(null)
let anim: AnimationItem | null = null

const destroy = () => {
  anim?.destroy()
  anim = null
}

const mount = () => {
  destroy()
  const el = containerRef.value
  if (!el || !props.active) return
  anim = lottie.loadAnimation({
    container: el,
    renderer: 'canvas',
    loop: true,
    autoplay: true,
    animationData,
    rendererSettings: {
      clearCanvas: true,
      preserveAspectRatio: 'xMidYMid meet',
    },
  })
  anim.setSpeed(2)
}

onMounted(mount)
onUnmounted(destroy)
watch(() => props.active, (active) => {
  if (active) mount()
  else destroy()
})
</script>
