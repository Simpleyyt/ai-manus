<template>
  <div
    class="flex items-center gap-3 p-3 h-[76px] rounded-[12px] border border-[var(--border-main)] clickable hover:bg-[var(--fill-tsp-white-light)]"
    data-testid="connector-catalog-card"
    @click="emit('connect', item)"
  >
    <div
      class="flex items-center justify-center size-10 bg-[var(--background-menu-white)] rounded-lg border border-[var(--border-main)] shrink-0"
    >
      <ConnectorIcon
        :uid="item.uid"
        :size="24"
        :default-icon-url="item.iconUrl"
        :default-icon-url-dark="item.iconUrlDark"
      />
    </div>
    <div class="flex flex-col items-start justify-center min-w-0 flex-1">
      <div class="w-full overflow-hidden">
        <div class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)] truncate">
          {{ item.name }}
        </div>
      </div>
      <p class="w-full text-[12px] font-normal leading-[16px] text-[var(--text-tertiary)] line-clamp-2">
        {{ item.brief }}
      </p>
    </div>
    <button
      type="button"
      data-testid="connector-catalog-connect"
      :title="t('Connect')"
      class="flex size-7 shrink-0 items-center justify-center rounded-[8px] border border-[var(--border-main)] clickable"
      @click.stop="emit('connect', item)"
    >
      <Plus :size="14" color="var(--icon-primary)" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'
import ConnectorIcon from './ConnectorIcon.vue'

defineProps<{
  item: ConnectorCatalogItem
}>()

const emit = defineEmits<{
  connect: [item: ConnectorCatalogItem]
}>()

const { t } = useI18n()
</script>
