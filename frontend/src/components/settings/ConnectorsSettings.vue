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
          {{ t('Browse connectors') }}
        </button>
        <button
          type="button"
          data-testid="connectors-add-custom-button"
          class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-8 min-w-[56px] px-3 rounded-[8px] gap-1 text-[13px] leading-[18px] bg-[var(--Button-black)] text-white clickable shrink-0"
          @click="customOpen = true"
        >
          {{ t('Add custom MCP') }}
        </button>
      </div>
    </div>

    <ConnectorsBrowseDialog v-model:open="browseOpen" />
    <CustomMCPDialog v-model:open="customOpen" />

    <div class="flex-1 space-y-6">
      <div v-if="filteredConnected.length === 0" class="h-full flex items-center justify-center">
        <p class="text-[14px] font-medium text-[var(--text-primary)] text-center">
          {{ t('No connectors yet') }}
        </p>
      </div>

      <template v-else>
        <div v-if="builtinConnected.length > 0" class="space-y-2">
          <p class="text-[13px] text-[var(--text-tertiary)]">{{ t('Connected') }}</p>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <ConnectorCard
              v-for="connector in builtinConnected"
              :key="connector.id"
              :connector="connector"
            />
          </div>
        </div>

        <div v-if="customConnected.length > 0" class="space-y-2">
          <p class="text-[13px] text-[var(--text-tertiary)]">{{ t('Custom MCP') }}</p>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <ConnectorCard
              v-for="connector in customConnected"
              :key="connector.id"
              :connector="connector"
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import ConnectorCard from '@/components/connectors/ConnectorCard.vue'
import ConnectorsBrowseDialog from '@/components/connectors/ConnectorsBrowseDialog.vue'
import CustomMCPDialog from '@/components/connectors/CustomMCPDialog.vue'
import { useConnectors } from '@/composables/useConnectors'

const { t } = useI18n()
const { connected, filterByQuery } = useConnectors()
const query = ref('')
const browseOpen = ref(false)
const customOpen = ref(false)

const filteredConnected = computed(() => filterByQuery(query.value, connected.value) as typeof connected.value)
const builtinConnected = computed(() =>
  filteredConnected.value.filter((connector) => connector.source === 'builtin'),
)
const customConnected = computed(() =>
  filteredConnected.value.filter((connector) => connector.source === 'custom'),
)
</script>
