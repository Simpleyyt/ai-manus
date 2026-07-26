<template>
  <!-- Inside session message column (already max-w-[810px]); span full column width -->
  <div
    v-if="visible"
    class="w-full mb-3 flex items-center gap-3 rounded-[14px] bg-[var(--background-menu-white)] px-4 py-3 shadow-[0px_8px_24px_0px_rgba(0,0,0,0.06)] border border-[var(--border-light)]">
    <div class="size-9 rounded-[10px] bg-[var(--fill-tsp-white-dark)] flex items-center justify-center shrink-0">
      <Monitor :size="18" class="text-[var(--icon-primary)]" />
    </div>
    <div class="flex-1 min-w-0 text-[14px] leading-[20px] text-[var(--text-primary)]">
      {{ t('You can choose to take over the browser to complete the operation.') }}
    </div>
    <button
      type="button"
      class="shrink-0 h-9 px-4 rounded-[100px] bg-[var(--Button-primary-black)] text-[var(--text-onblack)] text-sm font-medium hover:opacity-90"
      @click="emit('takeControl')">
      {{ t('Take control') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { Monitor } from 'lucide-vue-next';

defineProps<{ visible: boolean }>();
const emit = defineEmits<{ (e: 'takeControl'): void }>();
const { t } = useI18n();
</script>
