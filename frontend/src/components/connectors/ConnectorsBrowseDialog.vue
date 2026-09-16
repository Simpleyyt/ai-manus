<template>
  <Dialog v-model:open="open">
    <DialogContent
      class="flex h-[680px] w-[800px] max-w-[98%] flex-col overflow-hidden border border-[var(--border-main)] bg-[var(--background-gray-main)] p-0 shadow-menu"
    >
      <div class="flex min-h-0 flex-1 flex-col" data-testid="connectors-browse-dialog">
        <DialogHeader>
          <DialogTitle>{{ t('Connectors') }}</DialogTitle>
        </DialogHeader>

        <div class="flex min-h-0 flex-1 flex-col gap-3 px-6 pb-3">
          <div
            class="flex h-8 items-center gap-[6px] rounded-[8px] bg-[var(--fill-tsp-white-light)] px-2 focus-within:ring-1 focus-within:ring-[var(--border-input-active)]"
          >
            <Search :size="16" color="var(--icon-tertiary)" />
            <input
              v-model="query"
              type="text"
              :placeholder="t('Search connectors')"
              class="min-w-0 flex-1 border-none bg-transparent px-1 text-[14px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-disable)]"
            >
          </div>

          <div class="flex w-full flex-wrap items-center gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              class="h-8 px-3 py-1 text-[14px] font-medium clickable hover:opacity-80"
              :class="activeTab === tab.id
                ? 'rounded-[999px] bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)]'
                : 'rounded-[8px] text-[var(--text-tertiary)]'"
              @click="activeTab = tab.id"
            >
              {{ t(tab.labelKey) }}
            </button>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto">
            <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <ConnectorCard
                v-for="item in filteredCatalog"
                :key="item.id"
                :connector="item"
                mode="browse"
                :connected="isConnected(item.id)"
                @connect="openConnect(item)"
              />
            </div>
          </div>
        </div>
      </div>

      <ConnectBuiltinDialog
        v-model:open="connectOpen"
        :catalog-item="selectedCatalogItem"
      />
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import ConnectorCard from '@/components/connectors/ConnectorCard.vue'
import ConnectBuiltinDialog from '@/components/connectors/ConnectBuiltinDialog.vue'
import { useConnectors } from '@/composables/useConnectors'
import type { ConnectorCatalogItem } from '@/types/connector'

const open = defineModel<boolean>('open', { default: false })

const { t } = useI18n()
const { catalog, filterByQuery, isConnected } = useConnectors()
const query = ref('')
const activeTab = ref('all')
const connectOpen = ref(false)
const selectedCatalogItem = ref<ConnectorCatalogItem | null>(null)

const tabs = [
  { id: 'all', labelKey: 'All' },
  { id: 'productivity', labelKey: 'Productivity' },
  { id: 'business', labelKey: 'Business' },
  { id: 'development', labelKey: 'Development' },
]

const filteredCatalog = computed(() => {
  let items = filterByQuery(query.value, catalog.value) as ConnectorCatalogItem[]
  if (activeTab.value !== 'all') {
    items = items.filter((item) => item.category === activeTab.value)
  }
  return items
})

function openConnect(item: ConnectorCatalogItem) {
  selectedCatalogItem.value = item
  connectOpen.value = true
}
</script>
