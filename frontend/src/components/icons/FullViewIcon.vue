<script setup lang="ts">
withDefaults(defineProps<{
  color?: string
  size?: number | string
}>(), {
  color: 'var(--icon-secondary)',
  size: 16,
})
</script>

<template>
  <!-- Official FullViewIcon -->
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 18 14"
    fill="none"
    :width="size"
    :height="size"
    :color="color">
    <path
      d="M3.75 3.85C3.75 3.51863 4.01863 3.25 4.35 3.25L13.65 3.25C13.9814 3.25 14.25 3.51863 14.25 3.85L14.25 10.15C14.25 10.4814 13.9814 10.75 13.65 10.75L4.35 10.75C4.01863 10.75 3.75 10.4814 3.75 10.15L3.75 3.85Z"
      fill="currentColor" />
    <path
      d="M15.75 2.5C15.75 2.08579 15.4142 1.75 15 1.75L3 1.75C2.58579 1.75 2.25 2.08579 2.25 2.5L2.25 11.5C2.25 11.9142 2.58579 12.25 3 12.25L15 12.25C15.4142 12.25 15.75 11.9142 15.75 11.5L15.75 2.5ZM17.25 11.5C17.25 12.7426 16.2426 13.75 15 13.75L3 13.75C1.75736 13.75 0.75 12.7426 0.75 11.5L0.75 2.5C0.75 1.25736 1.75736 0.25 3 0.25L15 0.25C16.2426 0.25 17.25 1.25736 17.25 2.5L17.25 11.5Z"
      fill="currentColor" />
  </svg>
</template>
