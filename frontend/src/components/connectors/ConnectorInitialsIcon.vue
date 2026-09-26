<template>
  <span
    data-testid="connector-initials-icon"
    :style="{
      width: `${size}px`,
      height: `${size}px`,
      fontSize: `${fontSize}px`,
      lineHeight: `${size}px`,
    }"
    :class="cn(
      'flex items-center justify-center rounded font-medium text-[var(--text-secondary)] bg-[var(--fill-tsp-white-main)]',
      className,
    )"
  >{{ letter }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  name: string
  size?: number
  className?: string
}>(), {
  size: 16,
})

const letter = computed(() => props.name.charAt(0).toUpperCase())
const fontSize = computed(() => (
  props.size >= 24 ? 12 : Math.max(8, Math.floor(0.35 * props.size))
))
</script>
