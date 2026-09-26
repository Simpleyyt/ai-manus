<template>
  <Popover v-model:open="menuOpen">
    <PopoverTrigger as-child>
      <button
        type="button"
        data-testid="connectors-create-button"
        class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-8 min-w-[56px] px-3 rounded-[8px] gap-1 text-[13px] leading-[18px] outline outline-1 -outline-offset-1 hover:bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)] outline-[var(--Button-border-secondary)] bg-transparent clickable shrink-0"
        :aria-expanded="menuOpen"
        aria-haspopup="dialog"
      >
        {{ t('Create') }}
        <ChevronDown :size="16" color="var(--icon-primary)" />
      </button>
    </PopoverTrigger>
    <PopoverContent
      align="end"
      side="bottom"
      :side-offset="4"
      class="z-[1100] w-[220px] rounded-[12px] border-0 bg-[var(--background-menu-white)] p-1 shadow-menu"
      data-testid="connectors-create-menu"
    >
      <button
        type="button"
        data-testid="connectors-create-custom-mcp"
        class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
        @click="openForm()"
      >
        <Server :size="16" color="var(--icon-primary)" />
        <span class="truncate text-start">{{ t('Custom MCP') }}</span>
      </button>
      <button
        type="button"
        data-testid="connectors-create-import-json"
        class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
        @click="jsonOpen = true; menuOpen = false"
      >
        <Braces :size="16" color="var(--icon-primary)" />
        <span class="truncate text-start">{{ t('Import MCP by JSON') }}</span>
      </button>
      <div class="h-[1px] bg-[var(--border-main)] mx-[8px] my-1" />
      <button
        type="button"
        data-testid="connectors-create-by-url"
        class="flex w-full cursor-pointer items-center gap-[4px] rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
        @click="urlOpen = true; menuOpen = false"
      >
        <Globe :size="16" color="var(--icon-primary)" />
        <span class="truncate text-start">{{ t('Add MCP by URL') }}</span>
        <span
          class="shrink-0 h-[18px] flex items-center justify-center px-1.5 py-1 border border-[var(--border-dark)] rounded-tl-[8px] rounded-tr-[10px] rounded-br-[10px] text-[12px] font-medium leading-[16px] text-[var(--text-tertiary)]"
        >
          {{ t('Beta') }}
        </span>
      </button>
    </PopoverContent>
  </Popover>

  <ConfigureMcpFormDialog v-model:open="formOpen" @created="emit('created')" />
  <ImportMcpJsonDialog v-model:open="jsonOpen" @created="emit('created')" />
  <ConfigureMcpByUrlDialog v-model:open="urlOpen" @created="emit('created')" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Braces, ChevronDown, Globe, Server } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import ConfigureMcpFormDialog from './ConfigureMcpFormDialog.vue'
import ImportMcpJsonDialog from './ImportMcpJsonDialog.vue'
import ConfigureMcpByUrlDialog from './ConfigureMcpByUrlDialog.vue'

const emit = defineEmits<{
  created: []
}>()

const { t } = useI18n()
const menuOpen = ref(false)
const formOpen = ref(false)
const jsonOpen = ref(false)
const urlOpen = ref(false)

const openForm = () => {
  menuOpen.value = false
  formOpen.value = true
}
</script>
