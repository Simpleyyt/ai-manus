<template>
  <Dialog v-model:open="open">
    <DialogContent class="w-[560px] max-w-[98%] rounded-[16px] border border-[var(--border-main)] p-0 shadow-menu">
      <DialogHeader class="px-6 pt-6">
        <DialogTitle>{{ t('Connect {name}', { name: catalogItem?.name || '' }) }}</DialogTitle>
        <DialogDescription>
          {{ catalogItem?.description }}
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4 px-6 pb-6">
        <div
          v-for="field in envFields"
          :key="field.key"
          class="space-y-2"
        >
          <label class="text-[14px] font-medium text-[var(--text-primary)]">
            {{ field.label }}
          </label>
          <input
            v-model="envValues[field.key]"
            :type="field.secret ? 'password' : 'text'"
            :placeholder="field.placeholder || ''"
            class="flex h-9 w-full rounded-[8px] border border-[var(--Button-border-secondary)] bg-transparent px-3 text-[14px] outline-none focus:border-[var(--border-input-active)]"
          >
        </div>

        <div
          v-for="field in headerFields"
          :key="field.key"
          class="space-y-2"
        >
          <label class="text-[14px] font-medium text-[var(--text-primary)]">
            {{ field.label }}
          </label>
          <input
            v-model="headerValues[field.key]"
            :type="field.secret ? 'password' : 'text'"
            :placeholder="field.placeholder || ''"
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
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { ConnectorCatalogItem } from '@/types/connector'
import { connectBuiltin, testConnectorConnection } from '@/composables/connectorsStore'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const props = defineProps<{
  catalogItem: ConnectorCatalogItem | null
}>()

const open = defineModel<boolean>('open', { default: false })

const { t } = useI18n()
const envValues = ref<Record<string, string>>({})
const headerValues = ref<Record<string, string>>({})
const saving = ref(false)
const testing = ref(false)
const testMessage = ref('')
const testSuccess = ref(false)

const envFields = computed(() => props.catalogItem?.env_fields || [])
const headerFields = computed(() => props.catalogItem?.header_fields || [])

watch(open, (isOpen) => {
  if (!isOpen) return
  envValues.value = {}
  headerValues.value = {}
  testMessage.value = ''
  testSuccess.value = false
})

function buildPayload() {
  const env = Object.fromEntries(
    Object.entries(envValues.value).filter(([, value]) => value.trim()),
  )
  const headers = Object.fromEntries(
    Object.entries(headerValues.value).filter(([, value]) => value.trim()),
  )
  return { env, headers }
}

async function onTest() {
  if (!props.catalogItem) return
  testing.value = true
  testMessage.value = ''
  try {
    const { env, headers } = buildPayload()
    const result = await testConnectorConnection({
      transport: props.catalogItem.transport,
      command: props.catalogItem.command || undefined,
      args: props.catalogItem.args || undefined,
      url: props.catalogItem.url || undefined,
      env,
      headers,
    })
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
  if (!props.catalogItem) return
  saving.value = true
  try {
    const { env, headers } = buildPayload()
    await connectBuiltin(props.catalogItem.id, { env, headers })
    showSuccessToast(t('Connector connected'))
    open.value = false
  } catch (error) {
    showErrorToast(error instanceof Error ? error.message : t('Failed to connect connector'))
  } finally {
    saving.value = false
  }
}
</script>
