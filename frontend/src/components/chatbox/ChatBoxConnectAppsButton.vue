<template>
  <div class="relative" data-testid="chatbox-connect-apps">
    <Popover v-model:open="open">
      <PopoverTrigger as-child>
        <button
          ref="triggerRef"
          type="button"
          data-testid="chatbox-connect-apps-trigger"
          :title="t('Connect apps')"
          :data-popover-trigger="open ? 'true' : undefined"
          class='justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-[32px] text-[14px] leading-[18px] outline-1 -outline-offset-1 text-[var(--text-primary)] bg-transparent flex items-center gap-[4px] p-[8px] ps-[8px] cursor-pointer rounded-[100px] outline outline-[var(--border-main)] hover:bg-[var(--fill-tsp-white-light)] min-w-0 data-[popover-trigger="true"]:bg-[var(--fill-tsp-white-light)]'
        >
          <div class="flex items-center gap-[4px]">
            <template v-if="enabledIcons.length === 0">
              <Cable :size="16" color="var(--icon-secondary)" />
            </template>
            <template v-else>
              <ConnectorIcon
                v-for="item in enabledIcons.slice(0, maxIcons)"
                :key="item.id"
                :uid="item.id"
                :default-icon-url="item.icon_url"
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
        class="min-w-[250px] w-max max-w-[min(400px,var(--available-width))] rounded-[12px] bg-[var(--background-menu-white)] shadow-menu flex flex-col"
        :style="availableStyle"
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
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Cable } from 'lucide-vue-next'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { useConnectors } from '@/composables/useConnectors'
import { useSettingsDialog } from '@/composables/useSettingsDialog'
import type { Connector } from '@/types/connector'
import ChatBoxConnectorsPanel from './ChatBoxConnectorsPanel.vue'
import ConnectorIcon from '@/components/connectors/ConnectorIcon.vue'
import ConnectorsBrowseDialog from '@/components/connectors/ConnectorsBrowseDialog.vue'
import ConfigureMcpFormDialog from '@/components/connectors/ConfigureMcpFormDialog.vue'

const { t } = useI18n()
const { connectors } = useConnectors()
const { openSettingsDialog } = useSettingsDialog()

const open = ref(false)
const browseOpen = ref(false)
const formOpen = ref(false)
const editing = ref<Connector | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const availableBox = ref({ width: 400, height: 400 })
const maxIcons = 3

const enabledIcons = computed(() =>
  connectors.value.filter((item) => item.enabled),
)

const availableStyle = computed(() => ({
  minHeight: '200px',
  maxHeight: 'calc(var(--available-height) - 8px)',
  '--available-width': `${availableBox.value.width}px`,
  '--available-height': `${availableBox.value.height}px`,
}))

const measureAvailable = () => {
  const el = triggerRef.value
  if (!el || typeof window === 'undefined') return
  const rect = el.getBoundingClientRect()
  availableBox.value = {
    width: Math.max(250, Math.round(window.innerWidth - rect.left - 8)),
    height: Math.max(208, Math.round(window.innerHeight - rect.bottom - 8)),
  }
}

watch(open, (visible) => {
  if (visible) measureAvailable()
})

const onAdd = () => {
  open.value = false
  browseOpen.value = true
}

const onManage = () => {
  open.value = false
  openSettingsDialog('connectors')
}

const onConfigure = (connector: Connector) => {
  if (connector.readonly) return
  open.value = false
  editing.value = connector
  formOpen.value = true
}
</script>
