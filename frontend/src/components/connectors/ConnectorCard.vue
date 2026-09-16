<template>
  <div
    class="h-[76px] flex flex-col gap-3 p-3 rounded-[12px] border border-[var(--border-main)] clickable hover:bg-[var(--fill-tsp-white-light)]"
    data-testid="connector-card"
  >
    <div class="flex gap-3 items-center w-full">
      <div
        class="flex items-center justify-center size-10 bg-[var(--background-menu-white)] rounded-[8px] border border-[var(--border-main)] shrink-0 overflow-hidden"
      >
        <img
          v-if="connector.icon_url"
          :src="connector.icon_url"
          :alt="connector.name"
          class="size-5 object-contain"
        >
        <Plug v-else :size="20" color="var(--icon-primary)" />
      </div>
      <div class="flex flex-col items-start justify-center min-w-0 flex-1 h-[52px]">
        <div class="w-full flex gap-1 items-center">
          <p class="truncate text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
            {{ connector.name }}
          </p>
          <span
            v-if="'source' in connector && connector.source === 'builtin'"
            class="flex items-center shrink-0"
            :title="t('Official connector')"
          >
            <ShieldCheck :size="16" color="var(--icon-tertiary)" />
          </span>
        </div>
        <p class="w-full text-[12px] leading-[16px] text-[var(--text-tertiary)] line-clamp-2">
          {{ connector.description }}
        </p>
      </div>
      <div class="flex items-center gap-2" @click.stop>
        <button
          v-if="mode === 'browse' && !connected"
          type="button"
          data-testid="connector-card-connect"
          class="inline-flex h-8 min-w-[72px] items-center justify-center rounded-[8px] border border-[var(--border-main)] px-3 text-[13px] font-medium clickable"
          @click="emit('connect')"
        >
          {{ t('Connect') }}
        </button>
        <div
          v-else-if="mode === 'browse' && connected"
          class="flex size-8 shrink-0 items-center justify-center"
        >
          <Check :size="16" color="var(--icon-tertiary)" />
        </div>
        <template v-else>
          <button
            type="button"
            class="inline-flex size-7 items-center justify-center rounded-[8px] border border-[var(--border-main)] clickable"
            :title="t('Manage')"
            @click="emit('manage')"
          >
            <Settings2 :size="14" color="var(--icon-primary)" />
          </button>
          <SettingsSwitch
            v-model:checked="enabled"
            size="small"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Check, Plug, Settings2, ShieldCheck } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import SettingsSwitch from '@/components/settings/SettingsSwitch.vue'
import type { ConnectedConnector, ConnectorCatalogItem } from '@/types/connector'
import { setConnectorEnabled } from '@/composables/connectorsStore'

const props = withDefaults(defineProps<{
  connector: ConnectorCatalogItem | ConnectedConnector
  mode?: 'settings' | 'browse'
  connected?: boolean
}>(), {
  mode: 'settings',
  connected: true,
})

const emit = defineEmits<{
  connect: []
  manage: []
}>()

const { t } = useI18n()

const enabled = computed({
  get: () => (props.connector as ConnectedConnector).enabled ?? true,
  set: (value: boolean) => {
    const connectedConnector = props.connector as ConnectedConnector
    if (connectedConnector.id) {
      void setConnectorEnabled(connectedConnector.id, value)
    }
  },
})
</script>
