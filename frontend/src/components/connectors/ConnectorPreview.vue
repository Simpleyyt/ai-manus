<template>
  <div
    v-if="items.length > 0"
    class="flex items-center -space-x-1"
    data-testid="connector-preview"
  >
    <div
      v-for="item in items.slice(0, 2)"
      :key="item.uid"
      class="size-[24px] rounded-full border border-[var(--border-main)] bg-[var(--background-menu-white)] flex items-center justify-center"
    >
      <ConnectorIcon
        :uid="item.uid"
        :size="14"
        :default-icon-url="item.iconUrl"
        :default-icon-url-dark="item.iconUrlDark"
      />
    </div>
    <div
      v-if="items.length > 2"
      class="size-[24px] rounded-full border border-[var(--border-main)] bg-[var(--background-menu-white)] flex items-center justify-center"
    >
      <span class="text-[var(--text-tertiary)] text-[10px] leading-[16px]">
        +{{ Math.min(items.length - 2, 99) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { previewCatalogItems } from '@/data/connectorCatalog'
import ConnectorIcon from './ConnectorIcon.vue'

const items = computed(() => previewCatalogItems())
</script>
