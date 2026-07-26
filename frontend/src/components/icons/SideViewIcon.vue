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
  <!-- Official SideViewIcon -->
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 18 18"
    fill="none"
    :width="size"
    :height="size"
    :color="color">
    <path
      d="M8.25 5.85C8.25 5.51863 8.51863 5.25 8.85 5.25H13.65C13.9814 5.25 14.25 5.51863 14.25 5.85L14.25 12.15C14.25 12.4814 13.9814 12.75 13.65 12.75H8.85C8.51863 12.75 8.25 12.4814 8.25 12.15L8.25 5.85Z"
      fill="currentColor" />
    <path
      d="M15.75 4.5C15.75 4.08579 15.4142 3.75 15 3.75L3 3.75C2.58579 3.75 2.25 4.08579 2.25 4.5L2.25 13.5C2.25 13.9142 2.58579 14.25 3 14.25L15 14.25C15.4142 14.25 15.75 13.9142 15.75 13.5L15.75 4.5ZM17.25 13.5C17.25 14.7426 16.2426 15.75 15 15.75L3 15.75C1.75736 15.75 0.75 14.7426 0.75 13.5L0.75 4.5C0.75 3.25736 1.75736 2.25 3 2.25L15 2.25C16.2426 2.25 17.25 3.25736 17.25 4.5L17.25 13.5Z"
      fill="currentColor" />
  </svg>
</template>
