<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <rect width="24" height="24" rx="6" fill="var(--text-primary)" />
    <path
      d="M6.5 17V7h2.1l2.55 6.35L13.7 7H15.8v10h-1.85v-5.9L11.7 17h-1.55L7.9 11.1V17H6.5Z"
      fill="var(--background-gray-main)"
    />
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 24 })
</script>
