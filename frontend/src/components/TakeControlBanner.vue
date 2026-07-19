<template>
  <div
    v-if="visible"
    class="mx-auto w-full max-w-full sm:max-w-[768px] mb-3 flex items-center gap-3 rounded-[12px] border border-[var(--border-main)] bg-[var(--background-menu-white)] px-4 py-3 shadow-[0px_4px_16px_0px_rgba(0,0,0,0.04)]">
    <div class="size-9 rounded-[8px] bg-[var(--fill-tsp-white-dark)] flex items-center justify-center shrink-0">
      <Monitor :size="18" class="text-[var(--icon-primary)]" />
    </div>
    <div class="flex-1 min-w-0 text-sm text-[var(--text-primary)]">
      {{ t('You can choose to take over the browser to complete the operation.') }}
    </div>
    <button
      type="button"
      class="shrink-0 h-9 px-3 rounded-[10px] bg-[var(--Button-primary-black)] text-[var(--text-onblack)] text-sm font-medium hover:opacity-90"
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
