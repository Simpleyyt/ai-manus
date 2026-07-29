<template>
  <div class="space-y-6 w-full">
    <p class="text-[13px] text-[var(--text-tertiary)] leading-[18px]">
      {{ t('Shortcuts are shown for reference on this device.') }}
    </p>
    <div class="space-y-1">
      <div
        v-for="row in shortcuts"
        :key="row.id"
        class="flex items-center justify-between gap-4 py-3 border-b border-[var(--border-light)] last:border-transparent"
      >
        <span class="text-sm text-[var(--text-primary)]">{{ t(row.label) }}</span>
        <div class="flex items-center gap-1">
          <kbd
            v-for="(key, idx) in row.keys"
            :key="`${row.id}-${idx}`"
            class="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1.5 rounded-[6px] border border-[var(--border-dark)] bg-[var(--fill-tsp-white-main)] text-[12px] font-medium text-[var(--text-secondary)]"
          >
            {{ key }}
          </kbd>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const isMac = typeof navigator !== 'undefined'
  && /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent)

const shortcuts = computed(() => [
  {
    id: 'new-task',
    label: 'New task',
    keys: isMac ? ['⌘', 'K'] : ['Ctrl', 'K'],
  },
])
</script>
