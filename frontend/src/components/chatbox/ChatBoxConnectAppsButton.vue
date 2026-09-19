<template>
  <div class="relative" data-testid="chatbox-connect-apps">
    <Popover v-model:open="open">
      <PopoverTrigger as-child>
        <button
          type="button"
          data-testid="chatbox-connect-apps-trigger"
          :title="t('Connect apps')"
          :data-popover-trigger="open ? 'true' : undefined"
          class="justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-[32px] text-[14px] leading-[18px] outline-1 -outline-offset-1 text-[var(--text-primary)] bg-transparent flex items-center gap-[4px] p-[8px] ps-[8px] cursor-pointer rounded-[100px] outline outline-[var(--border-main)] hover:bg-[var(--fill-tsp-white-light)] min-w-0 data-[popover-trigger=true]:bg-[var(--fill-tsp-white-light)]"
        >
          <div class="flex items-center gap-[4px]">
            <template v-if="enabledIcons.length === 0">
              <Cable :size="16" color="var(--icon-secondary)" />
            </template>
            <template v-else>
              <ChatBoxConnectorIcon
                v-for="item in enabledIcons.slice(0, maxIcons)"
                :key="item.id"
                :connector="item"
                :size="16"
              />
              <span
                v-if="enabledIcons.length > maxIcons"
                class="text-[var(--text-tertiary)] text-[12px] leading-[16px] truncate"
              >+{{ enabledIcons.length - maxIcons }}</span>
            </template>
          </div>
        </button>
      </PopoverTrigger>
      <PopoverContent
        side="bottom"
        align="start"
        :side-offset="8"
        class="z-[9] min-w-[250px] w-max max-w-[min(400px,var(--available-width))] rounded-[12px] border-0 bg-[var(--background-menu-white)] p-0 shadow-menu flex flex-col"
        :style="{ minHeight: '200px', maxHeight: 'calc(var(--available-height, 70vh) - 8px)' }"
      >
        <ChatBoxConnectorsPanel
          :open="open"
          @add="onAdd"
          @manage="onManage"
          @configure="onConfigure"
        />
      </PopoverContent>
    </Popover>
    <ConnectorsBrowseDialog v-model:open="browseOpen" />
    <ConfigureMcpFormDialog
      v-model:open="formOpen"
      :connector="editing"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Cable } from 'lucide-vue-next'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { useConnectors } from '@/composables/useConnectors'
import { useSettingsDialog } from '@/composables/useSettingsDialog'
import type { Connector } from '@/types/connector'
import ChatBoxConnectorsPanel from './ChatBoxConnectorsPanel.vue'
import ChatBoxConnectorIcon from './ChatBoxConnectorIcon.vue'
import ConnectorsBrowseDialog from '@/components/connectors/ConnectorsBrowseDialog.vue'
import ConfigureMcpFormDialog from '@/components/connectors/ConfigureMcpFormDialog.vue'

const { t } = useI18n()
const { connectors } = useConnectors()
const { openSettingsDialog } = useSettingsDialog()

const open = ref(false)
const browseOpen = ref(false)
const formOpen = ref(false)
const editing = ref<Connector | null>(null)
const maxIcons = 3

const enabledIcons = computed(() =>
  connectors.value.filter((item) => item.enabled),
)

const onAdd = () => {
  open.value = false
  browseOpen.value = true
}

const onManage = () => {
  open.value = false
  openSettingsDialog('connectors')
}

const onConfigure = (connector: Connector) => {
  if (connector.readonly || connector.source === 'file') return
  open.value = false
  editing.value = connector
  formOpen.value = true
}
</script>
