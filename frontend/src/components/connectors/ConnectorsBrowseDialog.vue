<template>
  <Dialog v-model:open="open">
    <DialogContent
      class="flex h-[680px] w-[800px] max-w-[98%] flex-col overflow-hidden border border-[var(--border-main)] bg-[var(--background-gray-main)] p-0 shadow-menu"
    >
      <div class="flex min-h-0 flex-1 flex-col" data-testid="connectors-browse-dialog">
        <DialogHeader>
          <DialogTitle>{{ t('Connectors') }}</DialogTitle>
        </DialogHeader>

        <div class="flex min-h-0 flex-1 flex-col overflow-hidden -mt-[6px] pt-[8px]">
          <div class="flex flex-col gap-3 px-6 pb-3">
          <div
            class="flex items-center gap-[6px] h-9 px-2 rounded-[8px] bg-[var(--fill-tsp-white-light)] focus-within:ring-1 focus-within:ring-[var(--border-input-active)]"
          >
            <div class="flex items-center justify-center size-5 shrink-0">
              <Search :size="16" color="var(--icon-tertiary)" />
            </div>
            <input
              v-model="query"
              type="text"
              data-testid="connectors-browse-search"
              :aria-label="t('Search connectors')"
              :placeholder="t('Search connectors')"
              class="flex-1 min-w-0 bg-transparent outline-none border-none px-1 text-[14px] text-[var(--text-primary)] placeholder:text-[var(--text-disable)]"
            >
          </div>

          <div class="flex items-center justify-between w-full">
            <div class="flex flex-wrap items-center gap-2">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                type="button"
                :data-testid="`connectors-browse-tab-${tab.id}`"
                class="h-8 px-3 py-1 text-[14px] font-medium clickable hover:opacity-80"
                :class="activeTab === tab.id
                  ? 'rounded-[999px] bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)]'
                  : 'rounded-[8px] text-[var(--text-tertiary)]'"
                @click="activeTab = tab.id"
              >
                {{ t(tab.labelKey) }}
              </button>
            </div>
            <ConnectorsCreateMenu />
          </div>
          </div>

          <div class="flex-1 h-0 min-h-0">
          <div
            v-if="showCatalog"
            class="min-h-0 flex-1 overflow-y-auto"
          >
            <div
              v-if="catalogItems.length === 0"
              class="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 h-full"
            >
              <Search :size="32" color="var(--icon-tertiary)" />
              <p class="text-sm text-[var(--text-tertiary)]">
                {{ t('No matching connectors.') }}
              </p>
            </div>
            <div
              v-else
              class="flex flex-col gap-3 px-6 pb-6"
            >
              <div class="grid gap-3 md:grid-cols-2">
                <ConnectorCatalogCard
                  v-for="item in catalogItems"
                  :key="item.uid"
                  :item="item"
                />
              </div>
            </div>
          </div>

          <div
            v-else-if="activeTab === 'projects'"
            class="flex flex-col w-full h-full items-center justify-center"
          >
            <div class="flex flex-col items-center w-[320px] space-y-3">
              <div class="flex size-8 items-center justify-center">
                <Cable :size="32" color="var(--icon-tertiary)" />
              </div>
              <p class="text-center text-[13px] text-[var(--text-quaternary)]">
                {{ t('Publish your custom MCP and API connectors to share them with your projects.') }}
              </p>
            </div>
          </div>

          <div
            v-else-if="showEmpty"
            class="flex flex-col w-full h-full items-center justify-center gap-2.5"
          >
            <div class="flex size-8 items-center justify-center">
              <Cable :size="32" color="var(--icon-tertiary)" />
            </div>
            <p class="text-center text-[13px] leading-[22px] text-[var(--text-quaternary)]">
              {{ t('No custom MCP added yet.') }}
            </p>
          </div>

          <div
            v-else-if="filtered.length === 0"
            class="flex min-h-0 flex-1 flex-col items-center justify-center gap-3"
          >
            <Search :size="32" color="var(--icon-tertiary)" />
            <p class="text-sm text-[var(--text-tertiary)]">
              {{ t('No matching connectors.') }}
            </p>
          </div>

          <div v-else class="min-h-0 flex-1 overflow-y-auto">
            <div class="w-full pb-6 space-y-3 overflow-hidden">
              <div class="grid md:grid-cols-2 gap-3 w-full pb-6 px-6">
                <McpCard
                  v-for="connector in filtered"
                  :key="connector.id"
                  :connector="connector"
                  @edit="openEdit"
                  @delete="confirmDelete"
                />
              </div>
            </div>
          </div>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>

  <ConfigureMcpFormDialog
    v-model:open="editOpen"
    :connector="editing"
    @deleted="editing = null"
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Cable, Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useConnectors } from '@/composables/useConnectors'
import { deleteConnector, connectorErrorMessage } from '@/composables/connectorsStore'
import { useDialog } from '@/composables/useDialog'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import type { Connector } from '@/types/connector'
import {
  catalogByTab,
  filterCatalogByQuery,
  type ConnectorCatalogTab,
} from '@/data/connectorCatalog'
import McpCard from './McpCard.vue'
import ConnectorCatalogCard from './ConnectorCatalogCard.vue'
import ConnectorsCreateMenu from './ConnectorsCreateMenu.vue'
import ConfigureMcpFormDialog from './ConfigureMcpFormDialog.vue'

type BrowseTab = 'apps' | 'custom-api' | 'custom-mcp' | 'projects'

const open = defineModel<boolean>('open', { required: true })
const { t } = useI18n()
const { connectors, filterByQuery } = useConnectors()
const { showConfirmDialog } = useDialog()
const query = ref('')
const activeTab = ref<BrowseTab>('apps')
const editOpen = ref(false)
const editing = ref<Connector | null>(null)

const tabs: { id: BrowseTab; labelKey: string }[] = [
  { id: 'apps', labelKey: 'Apps' },
  { id: 'custom-api', labelKey: 'Custom API' },
  { id: 'custom-mcp', labelKey: 'Custom MCP' },
  { id: 'projects', labelKey: 'Projects' },
]

const customConnectors = computed(() =>
  connectors.value.filter((item) => item.source !== 'file'),
)

const filtered = computed(() => filterByQuery(query.value, customConnectors.value))
const showEmpty = computed(() => activeTab.value === 'custom-mcp' && customConnectors.value.length === 0)
const catalogTab = computed((): ConnectorCatalogTab | null => {
  if (activeTab.value === 'apps') return 'apps'
  if (activeTab.value === 'custom-api') return 'api'
  return null
})
const showCatalog = computed(() => catalogTab.value !== null)
const catalogItems = computed(() => {
  const tab = catalogTab.value
  if (!tab) return []
  return filterCatalogByQuery(query.value, catalogByTab(tab))
})

watch(open, (isOpen) => {
  if (isOpen) {
    query.value = ''
    activeTab.value = 'apps'
  }
})

const openEdit = (connector: Connector) => {
  editing.value = connector
  editOpen.value = true
}

const confirmDelete = (connector: Connector) => {
  showConfirmDialog({
    title: t('Delete MCP Connector'),
    content: t('Are you sure you want to delete this connector? If this connector is already published, deleting it will also unpublish it.'),
    confirmText: t('Delete'),
    confirmType: 'danger',
    onConfirm: async () => {
      try {
        await deleteConnector(connector.id)
        showSuccessToast(t('Successfully deleted connector'))
      } catch (error) {
        showErrorToast(connectorErrorMessage(error, t('Failed to import MCP connector')))
      }
    },
  })
}
</script>
