<template>
  <Dialog v-model:open="open">
    <DialogContent class="w-[560px] max-w-[98%] overflow-hidden rounded-[20px] p-0">
      <DialogHeader class="pt-5 px-5 pb-[10px] pe-8">
        <DialogTitle>{{ t('Import MCP by JSON') }}</DialogTitle>
      </DialogHeader>
      <div class="px-5 pb-5 space-y-3" data-testid="import-mcp-json-dialog">
        <textarea
          v-model="jsonText"
          data-testid="mcp-json-input"
          :placeholder="exampleJson"
          class="h-[280px] resize-none border-none rounded-[10px] overflow-auto text-sm leading-[22px] text-[var(--text-primary)] w-full font-mono placeholder:text-[var(--text-disable)] bg-[var(--fill-tsp-white-main)] pt-2 pr-3 pb-2 pl-4 focus:ring-[1.5px] focus:ring-[var(--border-dark)] outline-none"
        />
      </div>
      <div class="flex justify-end gap-3 p-5">
        <button
          type="button"
          class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg px-4 text-sm outline outline-1 -outline-offset-1 outline-[var(--Button-border-secondary)] hover:bg-[var(--fill-tsp-white-light)]"
          @click="open = false"
        >
          {{ t('Cancel') }}
        </button>
        <button
          type="button"
          class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg bg-[var(--Button-primary-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-40"
          :disabled="saving || !jsonText.trim()"
          data-testid="mcp-json-import"
          @click="onImport"
        >
          {{ t('Import') }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { importMcpJson, connectorErrorMessage } from '@/composables/connectorsStore'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const exampleJson = `{
  "mcpServers": {
    "stdio-server-example": {
      "command": "npx",
      "args": ["-y", "mcp-server-example"]
    }
  }
}`

const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ created: [] }>()
const { t } = useI18n()
const jsonText = ref('')
const saving = ref(false)

watch(open, (isOpen) => {
  if (isOpen) jsonText.value = ''
})

const onImport = async () => {
  saving.value = true
  try {
    await importMcpJson(jsonText.value)
    showSuccessToast(t('Successfully created connector'))
    open.value = false
    emit('created')
  } catch (error) {
    showErrorToast(connectorErrorMessage(error, t('Failed to import MCP connector')))
  } finally {
    saving.value = false
  }
}
</script>
