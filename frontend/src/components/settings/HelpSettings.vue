<template>
  <div class="space-y-6 w-full">
    <p class="text-[13px] text-[var(--text-tertiary)] leading-[18px]">
      {{ t('Find documentation and report issues.') }}
    </p>

    <div class="space-y-3">
      <a
        v-for="link in links"
        :key="link.href"
        :href="link.href"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center justify-between gap-3 rounded-[12px] border border-[var(--border-main)] px-4 py-3 hover:bg-[var(--fill-tsp-white-light)] transition-colors"
      >
        <div class="min-w-0">
          <div class="text-sm font-medium text-[var(--text-primary)]">{{ t(link.title) }}</div>
          <div class="text-[13px] text-[var(--text-tertiary)] leading-[18px] truncate">
            {{ link.href }}
          </div>
        </div>
        <ArrowUpRight :size="16" color="var(--icon-tertiary)" class="shrink-0" />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ArrowUpRight } from 'lucide-vue-next'

const { t } = useI18n()

const links = [
  {
    title: 'Documentation',
    href: 'https://docs.ai-manus.com/#/en/',
  },
  {
    title: 'GitHub Issues',
    href: 'https://github.com/simpleyyt/ai-manus/issues',
  },
]
</script>
