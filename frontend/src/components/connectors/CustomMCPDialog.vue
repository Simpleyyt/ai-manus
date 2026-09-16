<template>
  <Dialog v-model:open="open">
    <DialogContent class="w-[560px] max-w-[98%] rounded-[16px] border border-[var(--border-main)] p-0 shadow-menu">
      <DialogHeader class="px-6 pt-6">
        <DialogTitle>{{ t('Add custom MCP') }}</DialogTitle>
        <DialogDescription>
          {{ t('Connect Manus to your internal tools and proprietary systems') }}
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4 px-6 pb-6">
        <div class="space-y-2">
          <label class="text-[14px] font-medium text-[var(--text-primary)]">{{ t('Server name') }}</label>
          <input
            v-model="form.name"
            type="text"
            :placeholder="t('Internal CRM')"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
        </div>

        <div class="space-y-2">
          <label class="text-[14px] font-medium text-[var(--text-primary)]">{{ t('Transport type') }}</label>
          <select
            v-model="form.transport"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
            <option value="streamable-http">{{ t('HTTP') }}</option>
            <option value="sse">{{ t('SSE') }}</option>
            <option value="stdio">{{ t('Stdio') }}</option>
          </select>
        </div>

        <div v-if="form.transport === 'stdio'" class="space-y-2">
          <label class="text-[14px] font-medium text-[var(--text-primary)]">{{ t('Command') }}</label>
          <input
            v-model="form.command"
            type="text"
            placeholder="npx"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
        </div>

        <div v-if="form.transport === 'stdio'" class="space-y-2">
          <label class="text-[14px] font-medium text-[var(--text-primary)]">{{ t('Arguments') }}</label>
          <input
            v-model="argsText"
            type="text"
            placeholder="-y @modelcontextprotocol/server-filesystem /tmp"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
        </div>

        <div v-else class="space-y-2">
          <label class="text-[14px] font-medium text-[var(--text-primary)]">{{ t('Server URL') }}</label>
          <input
            v-model="form.url"
            type="url"
            placeholder="https://mcp.example.com/mcp"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
        </div>

        <div class="space-y-2">
          <label class="text-[14px] font-medium text-[var(--text-primary)]">{{ t('Authorization header') }}</label>
          <input
            v-model="authHeader"
            type="password"
            placeholder="Bearer your-token"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
        </div>

        <p
          v-if="testMessage"
          class="text-[13px]"
          :class="testSuccess ? 'text-[var(--text-green)]' : 'text-[var(--text-red)]'"
        >
          {{ testMessage }}
        </p>

        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            class="inline-flex h-9 items-center justify-center rounded-[8px] border border-[var(--border-main)] px-4 text-[14px] clickable"
            :disabled="testing"
            @click="onTest"
          >
            {{ testing ? t('Testing...') : t('Test connection') }}
          </button>
          <button
            type="button"
            class="inline-flex h-9 items-center justify-center rounded-[8px] bg-[var(--Button-black)] px-4 text-[14px] font-medium text-white clickable disabled:opacity-50"
            :disabled="saving"
            @click="onSave"
          >
            {{ saving ? t('Saving...') : t('Save') }}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { ConnectorTransport } from '@/types/connector'
import { createCustomConnector, testConnectorConnection } from '@/composables/connectorsStore'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const open = defineModel<boolean>('open', { default: false })

const { t } = useI18n()
const form = reactive({
  name: '',
  transport: 'streamable-http' as ConnectorTransport,
  command: 'npx',
  url: '',
})
const argsText = ref('')
const authHeader = ref('')
const saving = ref(false)
const testing = ref(false)
const testMessage = ref('')
const testSuccess = ref(false)

watch(open, (isOpen) => {
  if (!isOpen) return
  form.name = ''
  form.transport = 'streamable-http'
  form.command = 'npx'
  form.url = ''
  argsText.value = ''
  authHeader.value = ''
  testMessage.value = ''
  testSuccess.value = false
})

function buildPayload() {
  const args = argsText.value.trim() ? argsText.value.trim().split(/\s+/) : undefined
  const headers = authHeader.value.trim()
    ? { Authorization: authHeader.value.trim() }
    : undefined
  return {
    name: form.name.trim(),
    transport: form.transport,
    command: form.transport === 'stdio' ? form.command.trim() : undefined,
    args,
    url: form.transport === 'stdio' ? undefined : form.url.trim(),
    headers,
  }
}

async function onTest() {
  testing.value = true
  testMessage.value = ''
  try {
    const result = await testConnectorConnection(buildPayload())
    testSuccess.value = result.success
    testMessage.value = result.success
      ? t('Connection successful ({count} tools)', { count: result.tools.length })
      : result.message
  } catch (error) {
    testSuccess.value = false
    testMessage.value = error instanceof Error ? error.message : t('Connection failed')
  } finally {
    testing.value = false
  }
}

async function onSave() {
  saving.value = true
  try {
    await createCustomConnector(buildPayload())
    showSuccessToast(t('Custom MCP added'))
    open.value = false
  } catch (error) {
    showErrorToast(error instanceof Error ? error.message : t('Failed to add custom MCP'))
  } finally {
    saving.value = false
  }
}
</script>
