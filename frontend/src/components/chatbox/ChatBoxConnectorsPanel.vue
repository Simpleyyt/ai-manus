<template>
  <div
    data-testid="chatbox-connectors-panel"
    class="flex min-h-0 flex-1 flex-col"
  >
    <div
      class="relative flex-1 min-h-0 overflow-y-auto p-[4px]"
    >
      <div
        v-for="connector in connectors"
        :key="connector.id"
        class="group/connector-item flex items-center gap-[8px] justify-between px-[8px] ps-[4px] h-[36px] rounded-[8px] cursor-pointer select-none hover:bg-[var(--fill-tsp-white-main)]"
        :data-testid="`chatbox-connector-${connector.id}`"
        @click="onRowClick(connector)"
      >
        <div class="flex items-center gap-[4px] overflow-hidden min-w-0">
          <div class="size-[28px] flex items-center justify-center flex-shrink-0">
            <ConnectorIcon :uid="connector.id" :size="16" />
          </div>
          <span
            class="text-[var(--text-primary)] text-sm leading-[20px] truncate"
            :title="connector.name"
          >{{ connector.name }}</span>
        </div>
        <div class="flex items-center gap-[4px]">
          <div
            v-if="canConfigure(connector)"
            class="flex opacity-0 pointer-events-none group-hover/connector-item:opacity-100 group-hover/connector-item:pointer-events-auto size-[28px] items-center justify-center rounded-[6px] hover:bg-[var(--fill-tsp-white-light)]"
            data-testid="chatbox-connector-configure"
            @click.stop="emit('configure', connector)"
          >
            <Settings2 :size="16" color="var(--icon-primary)" />
          </div>
          <div
            v-if="canToggle(connector)"
            @click.stop
          >
            <SettingsSwitch
              :checked="connector.enabled"
              size="medium"
              @checked-change="(value) => onToggle(connector, value)"
            />
          </div>
        </div>
      </div>
      <div
        class="sticky bottom-[-4px] start-0 w-full h-[36px] pointer-events-none"
        style="background: linear-gradient(to top, var(--background-menu-white) 0%, var(--gradual-white-0) 100%);"
      />
    </div>
    <div class="flex flex-col py-[4px] border-t border-[var(--border-main)]">
      <div class="px-[4px]">
        <div
          class="flex items-center justify-between px-[8px] h-[36px] rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer"
          data-close-when-click="true"
          data-testid="chatbox-connectors-add"
          @click="emit('add')"
        >
          <div class="flex items-center gap-[8px]">
            <div class="size-[20px] flex items-center justify-center">
              <Plus :size="16" color="var(--icon-primary)" />
            </div>
            <span class="text-[14px] text-[var(--text-primary)]">{{ t('Add connectors') }}</span>
          </div>
        </div>
      </div>
      <div v-if="hasInstalled" class="px-[4px]">
        <div
          class="flex items-center gap-[8px] px-[8px] h-[36px] rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer"
          data-close-when-click="true"
          data-testid="chatbox-connectors-manage"
          @click="emit('manage')"
        >
          <div class="size-[20px] flex items-center justify-center">
            <Settings2 :size="16" color="var(--icon-primary)" />
          </div>
          <span class="text-[14px] text-[var(--text-primary)]">{{ t('Manage connectors') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Settings2 } from 'lucide-vue-next'
import { useConnectors } from '@/composables/useConnectors'
import { setConnectorEnabled, connectorErrorMessage } from '@/composables/connectorsStore'
import type { Connector } from '@/types/connector'
import SettingsSwitch from '@/components/settings/SettingsSwitch.vue'
import ConnectorIcon from '@/components/connectors/ConnectorIcon.vue'
import { showErrorToast } from '@/utils/toast'

const props = defineProps<{
  open?: boolean
}>()

const emit = defineEmits<{
  (e: 'add'): void
  (e: 'manage'): void
  (e: 'configure', connector: Connector): void
}>()

const { t } = useI18n()
const { connectors, ensureConnectorsLoaded } = useConnectors()
const hasInstalled = computed(() => connectors.value.length > 0)

const canToggle = (connector: Connector) =>
  !connector.readonly && connector.source !== 'file'

const canConfigure = (connector: Connector) => canToggle(connector)

watch(
  () => props.open,
  async (open) => {
    if (open) await ensureConnectorsLoaded()
  },
  { immediate: true },
)

const onRowClick = (connector: Connector) => {
  if (canToggle(connector)) {
    void onToggle(connector, !connector.enabled)
  }
}

const onToggle = async (connector: Connector, enabled: boolean) => {
  if (!canToggle(connector) || connector.enabled === enabled) return
  try {
    await setConnectorEnabled(connector.id, enabled)
  } catch (error) {
    showErrorToast(connectorErrorMessage(error, t('Failed to import MCP connector')))
  }
}
</script>
