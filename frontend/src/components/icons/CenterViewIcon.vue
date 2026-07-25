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
  <!-- Official CenterViewIcon -->
  <svg
    viewBox="0 0 18 18"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    :color="color">
    <path
      d="M5.25 6.6C5.25 6.26863 5.51863 6 5.85 6H12.15C12.4814 6 12.75 6.26863 12.75 6.6V11.4C12.75 11.7314 12.4814 12 12.15 12H5.85C5.51863 12 5.25 11.7314 5.25 11.4V6.6Z"
      fill="currentColor" />
    <path
      d="M15.75 4.5C15.75 4.08579 15.4142 3.75 15 3.75H3C2.58579 3.75 2.25 4.08579 2.25 4.5V13.5C2.25 13.9142 2.58579 14.25 3 14.25H15C15.4142 14.25 15.75 13.9142 15.75 13.5V4.5ZM17.25 13.5C17.25 14.7426 16.2426 15.75 15 15.75H3C1.75736 15.75 0.75 14.7426 0.75 13.5V4.5C0.75 3.25736 1.75736 2.25 3 2.25H15C16.2426 2.25 17.25 3.25736 17.25 4.5V13.5Z"
      fill="currentColor" />
  </svg>
</template>
