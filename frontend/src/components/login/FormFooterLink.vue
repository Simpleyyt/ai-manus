<template>
  <div class="text-center text-[13px] leading-[18px] text-[var(--text-tertiary)] mt-[8px]">
    <span>{{ text }}</span>
    <span
      class="ms-[8px] text-[var(--text-secondary)] cursor-pointer select-none hover:opacity-80 active:opacity-70 transition-all underline"
      @click="$emit('action')">
      {{ linkText }}
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  text: string
  linkText: string
}>()

defineEmits<{
  action: []
}>()
</script>
