<template>
  <button type="submit"
    class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-[40px] px-[16px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full"
    :class="enabled && !loading
      ? 'bg-[var(--Button-primary-black)] text-[var(--text-onblack)] hover:opacity-90 active:opacity-80'
      : 'bg-[#898988] dark:bg-[#939393] text-[var(--text-onblack)] opacity-50 cursor-not-allowed'"
    :disabled="!enabled || loading">
    <LoaderCircle v-if="loading" :size="16" class="animate-spin" />
    <span>{{ loading ? loadingLabel : label }}</span>
  </button>
</template>

<script setup lang="ts">
import { LoaderCircle } from 'lucide-vue-next'

defineProps<{
  enabled: boolean
  loading: boolean
  label: string
  loadingLabel: string
}>()
</script>
