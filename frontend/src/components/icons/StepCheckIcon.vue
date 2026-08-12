<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 7 5"
    fill="none"
    :width="size"
    :height="size"
    :style="{ color }"
  >
    <path
      d="M5.83333 0.5L2.16667 4.16667L0.5 2.5"
      stroke="currentColor"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: number
    color?: string
  }>(),
  {
    size: 16,
    color: 'var(--icon-tertiary)',
  },
)
</script>
