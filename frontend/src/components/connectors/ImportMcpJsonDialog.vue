<template>
  <Dialog v-model:open="open">
    <DialogContent
      class="h-[458px] w-[600px] max-w-[98%] flex flex-col bg-[var(--background-gray-main)] overflow-hidden p-0"
    >
      <DialogHeader class="pt-5 px-5 pb-[10px] pe-8">
        <DialogTitle>{{ t('Import by JSON') }}</DialogTitle>
        <p class="text-[13px] leading-[18px] text-[var(--text-tertiary)]">
          {{ t('Please paste your configuration JSON') }}
        </p>
      </DialogHeader>
      <div
        class="flex flex-col flex-1 gap-[20px] px-[20px] pb-[20px] pt-0"
        data-testid="import-mcp-json-dialog"
      >
        <textarea
          v-model="jsonText"
          data-testid="mcp-json-input"
          :placeholder="exampleJson"
          class="h-full resize-none border-none rounded-[10px] text-sm leading-[22px] text-[var(--text-primary)] w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-tsp-white-main)] pt-2 pr-3 pb-2 pl-4 focus:ring-[1.5px] focus:ring-[var(--border-dark)] outline-none"
        />
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg bg-[var(--Button-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-40"
            :disabled="saving || !jsonText.trim()"
            data-testid="mcp-json-import"
            @click="onImport"
          >
            {{ t('Import') }}
          </button>
        </div>
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

const exampleJson = `// You can use either format:
// STDIO example:
{
  "mcpServers": {
    "stdio-server-example": {
      "command": "npx",
      "args": ["-y", "mcp-server-example"]
    }
  }
}

// SSE example:
{
  "mcpServers": {
    "sse-server-example": {
      "type": "sse",
      "url": "http://localhost:3000"
    }
  }
}


// HTTP example:
{
  "mcpServers": {
    "http-server-example": {
      "type": "streamableHttp",
      "url": "http://localhost:3001",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-token"
      }
    }
  }
}
`

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
