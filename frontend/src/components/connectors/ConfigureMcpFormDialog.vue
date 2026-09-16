<template>
  <Dialog v-model:open="open">
    <DialogContent class="w-[560px] max-w-[98%] overflow-hidden rounded-[20px] p-0">
      <DialogHeader class="pt-5 px-5 pb-[10px] pe-8">
        <DialogTitle>{{ connector ? t('Edit MCP') : t('Custom MCP') }}</DialogTitle>
      </DialogHeader>

      <div class="px-5 pb-5 space-y-4 max-h-[70vh] overflow-y-auto" data-testid="configure-mcp-form">
        <div class="flex gap-3">
          <div class="flex flex-col gap-2 flex-1">
            <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)] tracking-[-0.154px]">
              {{ t('Server Name') }}
            </label>
            <input
              v-model="form.name"
              type="text"
              data-testid="mcp-form-name"
              :placeholder="t('e.g., My Custom Server')"
              class="flex px-4 py-2 items-center gap-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
            >
          </div>
          <div class="flex flex-col gap-2 flex-1">
            <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)] tracking-[-0.154px]">
              {{ t('Transport Type') }}
            </label>
            <select
              v-model="form.transport"
              data-testid="mcp-form-transport"
              class="flex px-4 py-2 items-center gap-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)]"
            >
              <option value="stdio">STDIO</option>
              <option value="streamable-http">HTTP</option>
              <option value="sse">SSE</option>
            </select>
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
            {{ t('Note') }}<span class="text-[var(--text-tertiary)] font-normal">{{ t(' (optional)') }}</span>
          </label>
          <textarea
            v-model="form.note"
            data-testid="mcp-form-note"
            :placeholder="t('Provide MCP docs or instructions to tell {product} how and when to use this MCP', { product: 'Manus' })"
            class="h-[100px] resize-none border-none rounded-[10px] text-sm leading-[22px] text-[var(--text-primary)] w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-tsp-white-main)] pt-2 pr-3 pb-2 pl-4 focus:ring-[1.5px] focus:ring-[var(--border-dark)] outline-none"
          />
        </div>

        <div
          v-if="form.transport === 'streamable-http' || form.transport === 'sse'"
          class="flex flex-col gap-2"
        >
          <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)] tracking-[-0.154px]">
            {{ t('Server URL') }}
          </label>
          <input
            v-model="form.url"
            type="text"
            data-testid="mcp-form-url"
            :placeholder="form.transport === 'streamable-http' ? 'https://mcp.yourserver.com/mcp' : 'https://mcp.yourserver.com/sse'"
            class="flex px-4 py-2 items-center gap-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
          >
        </div>

        <template v-if="form.transport === 'stdio'">
          <div class="flex flex-col gap-2">
            <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)] tracking-[-0.154px]">
              {{ t('Command') }}
            </label>
            <input
              v-model="form.command"
              type="text"
              data-testid="mcp-form-command"
              placeholder="npx"
              class="flex px-4 py-2 items-center gap-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
            >
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)] tracking-[-0.154px]">
              {{ t('Arguments') }}
            </label>
            <div class="flex flex-col gap-2">
              <input
                v-for="(_, index) in form.args"
                :key="index"
                v-model="form.args[index]"
                type="text"
                :data-testid="`mcp-form-arg-${index}`"
                placeholder="-y"
                class="flex px-4 py-2 items-center gap-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
              >
              <button
                type="button"
                class="shrink-0 self-start inline-flex items-center gap-1 h-8 px-3 rounded-[8px] text-[13px] outline outline-1 -outline-offset-1 outline-[var(--Button-border-secondary)] hover:bg-[var(--fill-tsp-white-light)]"
                @click="form.args.push('')"
              >
                <Plus :size="16" />
                {{ t('Add argument') }}
              </button>
            </div>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
              {{ t('Environment variables') }}
            </label>
            <div class="flex flex-col gap-4">
              <div
                v-for="(item, index) in form.env"
                :key="index"
                class="group relative border border-[var(--border-main)] border-solid rounded-[12px] p-4"
              >
                <div class="flex flex-col gap-2 mb-4">
                  <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
                    {{ t('Secret name') }}
                  </label>
                  <input
                    v-model="item.key"
                    type="text"
                    placeholder="SOME_UNIQUE_KEY_NAME"
                    class="flex px-4 py-2 items-center rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-sm outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
                  >
                </div>
                <div class="flex flex-col gap-2">
                  <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
                    {{ t('Value') }}
                  </label>
                  <input
                    v-model="item.value"
                    type="password"
                    placeholder="Value of the secret, such as sk-example-1234"
                    class="flex px-4 py-2 items-center rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-sm outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
                  >
                </div>
              </div>
              <button
                type="button"
                class="shrink-0 self-start inline-flex items-center gap-1 h-8 px-3 rounded-[8px] text-[13px] outline outline-1 -outline-offset-1 outline-[var(--Button-border-secondary)] hover:bg-[var(--fill-tsp-white-light)]"
                @click="form.env.push({ key: '', value: '' })"
              >
                <Plus :size="16" />
                {{ t('Add secret') }}
              </button>
            </div>
          </div>
        </template>

        <div
          v-if="form.transport === 'streamable-http' || form.transport === 'sse'"
          class="flex flex-col gap-2"
        >
          <label class="text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
            {{ t('Headers') }}
          </label>
          <div class="flex flex-col gap-2">
            <div
              v-for="(item, index) in form.headers"
              :key="index"
              class="flex gap-2"
            >
              <input
                v-model="item.key"
                type="text"
                placeholder="Authorization"
                class="flex-1 px-4 py-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] h-[36px] border-none text-sm outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
              >
              <input
                v-model="item.value"
                type="text"
                placeholder="Bearer your-token"
                class="flex-1 px-4 py-2 rounded-[10px] bg-[var(--fill-tsp-white-main)] h-[36px] border-none text-sm outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
              >
            </div>
            <button
              type="button"
              class="shrink-0 self-start inline-flex items-center gap-1 h-8 px-3 rounded-[8px] text-[13px] outline outline-1 -outline-offset-1 outline-[var(--Button-border-secondary)] hover:bg-[var(--fill-tsp-white-light)]"
              @click="form.headers.push({ key: '', value: '' })"
            >
              <Plus :size="16" />
              {{ t('Add header') }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="connector" class="flex justify-between p-5">
        <button
          type="button"
          class="inline-flex items-center gap-2 h-9 px-3 rounded-[10px] text-sm outline outline-1 -outline-offset-1 outline-[var(--Button-secondary-error-border)] bg-[var(--Button-secondary-error-fill)] text-[var(--function-error)]"
          :disabled="saving"
          @click="onDelete"
        >
          <Trash2 :size="16" />
          {{ t('Delete') }}
        </button>
        <button
          type="button"
          class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg bg-[var(--Button-primary-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-40"
          :disabled="saving || !canSave"
          data-testid="mcp-form-save"
          @click="onSave"
        >
          {{ t('Save') }}
        </button>
      </div>
      <div v-else class="flex justify-end gap-3 p-5">
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
          :disabled="saving || !canSave"
          data-testid="mcp-form-save"
          @click="onSave"
        >
          {{ t('Save') }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Plus, Trash2 } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import type { Connector, ConnectorTransport, VariableItem } from '@/types/connector'
import {
  createConnector,
  deleteConnector,
  updateConnector,
  connectorErrorMessage,
} from '@/composables/connectorsStore'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { useDialog } from '@/composables/useDialog'

const open = defineModel<boolean>('open', { required: true })
const props = defineProps<{
  connector?: Connector | null
}>()
const emit = defineEmits<{
  created: []
  deleted: []
}>()

const { t } = useI18n()
const { showConfirmDialog } = useDialog()
const saving = ref(false)

const form = reactive({
  name: '',
  note: '',
  transport: 'stdio' as ConnectorTransport,
  command: '',
  args: [''] as string[],
  env: [{ key: '', value: '' }] as VariableItem[],
  url: '',
  headers: [{ key: '', value: '' }] as VariableItem[],
})

const canSave = computed(() => {
  if (!form.name.trim()) return false
  if (form.transport === 'stdio') return Boolean(form.command.trim())
  return Boolean(form.url.trim())
})

watch(open, (isOpen) => {
  if (!isOpen) return
  const current = props.connector
  form.name = current?.name || ''
  form.note = current?.note || ''
  form.transport = current?.transport || 'stdio'
  form.command = current?.command || ''
  form.args = current?.args?.length ? [...current.args] : ['']
  form.env = current?.env?.length ? current.env.map((item) => ({ ...item })) : [{ key: '', value: '' }]
  form.url = current?.url || ''
  form.headers = current?.headers?.length
    ? current.headers.map((item) => ({ ...item }))
    : [{ key: '', value: '' }]
})

const payload = () => ({
  name: form.name.trim(),
  note: form.note.trim() || null,
  transport: form.transport,
  command: form.transport === 'stdio' ? form.command.trim() : null,
  args: form.transport === 'stdio' ? form.args.filter((item) => item.trim()) : null,
  env: form.transport === 'stdio'
    ? form.env.filter((item) => item.key.trim())
    : null,
  url: form.transport === 'stdio' ? null : form.url.trim(),
  headers: form.transport === 'stdio'
    ? null
    : form.headers.filter((item) => item.key.trim()),
})

const onSave = async () => {
  saving.value = true
  try {
    if (props.connector) {
      await updateConnector(props.connector.id, payload())
      showSuccessToast(t('Successfully updated connector'))
    } else {
      await createConnector(payload())
      showSuccessToast(t('Successfully created connector'))
    }
    open.value = false
    emit('created')
  } catch (error) {
    showErrorToast(connectorErrorMessage(error, t('Failed to import MCP connector')))
  } finally {
    saving.value = false
  }
}

const onDelete = () => {
  if (!props.connector) return
  const id = props.connector.id
  showConfirmDialog({
    title: t('Delete MCP Connector'),
    content: t('Are you sure you want to delete this connector? If this connector is already published, deleting it will also unpublish it.'),
    confirmText: t('Delete'),
    confirmType: 'danger',
    onConfirm: async () => {
      try {
        await deleteConnector(id)
        showSuccessToast(t('Successfully deleted connector'))
        open.value = false
        emit('deleted')
      } catch (error) {
        showErrorToast(connectorErrorMessage(error, t('Failed to import MCP connector')))
      }
    },
  })
}
</script>
