<template>
  <div class="flex flex-col items-center justify-center gap-3 px-0 py-0 flex-1 min-h-0 h-full">
    <svg
      class="w-[160px] h-[160px] text-[var(--text-disable)]"
      viewBox="0 0 160 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      :aria-label="label">
      <rect x="28" y="36" width="104" height="72" rx="8" stroke="currentColor" stroke-width="3" fill="var(--fill-tsp-gray-main)" />
      <rect x="40" y="48" width="80" height="48" rx="4" fill="var(--background-menu-white)" stroke="currentColor" stroke-width="1.5" opacity="0.5" />
      <path d="M64 108h32v8a8 8 0 0 1-8 8H72a8 8 0 0 1-8-8v-8z" fill="currentColor" opacity="0.35" />
      <rect x="52" y="124" width="56" height="6" rx="3" fill="currentColor" opacity="0.25" />
      <circle cx="112" cy="56" r="3" fill="var(--function-success)" opacity="0.35" />
    </svg>
    <div class="text-center text-[var(--text-tertiary)] text-sm font-medium">
      {{ label }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const label = computed(() => t("{name}'s computer is inactive", { name: 'Manus' }));
</script>
