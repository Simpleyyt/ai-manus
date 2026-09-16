<template>
  <div class="flex flex-col h-full space-y-3 py-6 w-full" data-testid="connectors-settings">
    <div class="flex items-center justify-between gap-3 w-full">
      <div
        class="group rounded-[8px] overflow-hidden text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disable)] h-8 flex items-center px-3 w-[200px] border border-[var(--Button-border-secondary)] bg-transparent ps-3 pe-3 py-1 gap-1.5 focus-within:border-[var(--border-input-active)] shrink-0"
      >
        <Search :size="16" class="shrink-0 text-[var(--icon-tertiary)]" />
        <input
          v-model="query"
          type="text"
          data-testid="connectors-search-input"
          :placeholder="t('Search connectors')"
          class="h-full min-w-1 flex-1 bg-transparent disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] outline-none"
        >
      </div>
      <div class="flex gap-2 items-center shrink-0">
        <button
          type="button"
          data-testid="connectors-browse-button"
          class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-8 min-w-[56px] px-3 rounded-[8px] gap-1 text-[13px] leading-[18px] outline outline-1 -outline-offset-1 hover:bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)] outline-[var(--Button-border-secondary)] bg-transparent clickable shrink-0"
          @click="browseOpen = true"
        >
          {{ t('Browse Connectors') }}
        </button>
        <ConnectorsCreateMenu />
      </div>
    </div>

    <ConnectorsBrowseDialog v-model:open="browseOpen" />
    <ConfigureMcpFormDialog
      v-model:open="editOpen"
      :connector="editing"
      @deleted="editing = null"
    />

    <div class="flex-1">
      <div
        v-if="noQueryMatches"
        class="h-full flex items-center justify-center"
      >
        <p class="text-[14px] font-medium text-[var(--text-primary)] text-center">
          {{ t('No matching connectors.') }}
        </p>
      </div>
      <div
        v-else-if="!hasQuery && visible.length === 0"
        class="h-full flex flex-col"
      >
        <div class="flex flex-col items-center justify-center flex-1 gap-4 py-10">
          <div class="flex flex-col items-center gap-3">
            <Cable :size="32" color="var(--icon-tertiary)" />
            <p class="text-[14px] text-[var(--text-tertiary)] text-center">
              {{ t('Connect {product} with your everyday apps, APIs and MCPs', { product: 'Manus' }) }}
            </p>
          </div>
          <button
            type="button"
            data-testid="connectors-add-button"
            class="inline-flex items-center justify-center whitespace-nowrap font-medium h-9 px-3 rounded-[8px] gap-1 text-sm outline outline-1 -outline-offset-1 outline-[var(--Button-border-secondary)] hover:bg-[var(--fill-tsp-white-light)]"
            @click="browseOpen = true"
          >
            <Plus :size="16" color="var(--icon-primary)" />
            {{ t('Add connectors') }}
          </button>
        </div>
      </div>
      <div
        v-else
        class="grid grid-cols-1 gap-3 md:grid-cols-2"
      >
        <McpCard
          v-for="connector in visible"
          :key="connector.id"
          :connector="connector"
          @edit="openEdit"
          @delete="confirmDelete"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Cable, Plus, Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { useConnectors } from '@/composables/useConnectors'
import { deleteConnector, connectorErrorMessage } from '@/composables/connectorsStore'
import { useDialog } from '@/composables/useDialog'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import type { Connector } from '@/types/connector'
import McpCard from '@/components/connectors/McpCard.vue'
import ConnectorsCreateMenu from '@/components/connectors/ConnectorsCreateMenu.vue'
import ConnectorsBrowseDialog from '@/components/connectors/ConnectorsBrowseDialog.vue'
import ConfigureMcpFormDialog from '@/components/connectors/ConfigureMcpFormDialog.vue'

const { t } = useI18n()
const { connectors, filterByQuery } = useConnectors()
const { showConfirmDialog } = useDialog()
const query = ref('')
const browseOpen = ref(false)
const editOpen = ref(false)
const editing = ref<Connector | null>(null)

const hasQuery = computed(() => query.value.trim().length > 0)
const visible = computed(() => filterByQuery(query.value, connectors.value))
const noQueryMatches = computed(() => hasQuery.value && visible.value.length === 0)

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
