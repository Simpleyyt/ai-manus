<template>
  <Dialog v-model:open="open">
    <DialogContent class="w-[480px] max-w-[98%] overflow-hidden bg-[var(--background-gray-main)] p-0">
      <DialogHeader class="pt-5 px-5 pb-[10px] pe-8">
        <DialogTitle>{{ t('Enter the required API key to connect {name}', { name: item?.name || '' }) }}</DialogTitle>
      </DialogHeader>
      <div
        v-if="item"
        class="space-y-4 px-5 pb-5"
        data-testid="catalog-mcp-secrets-dialog"
      >
        <div
          v-for="field in item.requiredHeaders"
          :key="field.key"
          class="flex flex-col gap-2"
        >
          <label class="flex items-center gap-1 text-[14px] font-medium text-[var(--text-primary)]">
            {{ field.label }}
            <span class="text-[13px] text-[var(--function-error)]">*</span>
          </label>
          <input
            v-model="values[field.key]"
            type="password"
            :data-testid="`catalog-secret-${field.key}`"
            :placeholder="field.placeholder || field.label"
            class="flex px-4 py-2 items-center rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
          >
        </div>
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
          class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg bg-[var(--Button-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-40"
          :disabled="saving || !canSave"
          data-testid="catalog-secret-save"
          @click="onSave"
        >
          {{ t('Connect') }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'
import type { VariableItem } from '@/types/connector'

const open = defineModel<boolean>('open', { required: true })
const props = defineProps<{
  item: ConnectorCatalogItem | null
}>()
const emit = defineEmits<{
  submit: [headers: VariableItem[]]
}>()

const { t } = useI18n()
const saving = ref(false)
const values = reactive<Record<string, string>>({})

watch(open, (isOpen) => {
  if (!isOpen) return
  Object.keys(values).forEach((key) => {
    delete values[key]
  })
  for (const field of props.item?.requiredHeaders || []) {
    values[field.key] = ''
  }
})

const canSave = computed(() => (
  Boolean(props.item?.requiredHeaders.length)
  && (props.item?.requiredHeaders || []).every((field) => Boolean(values[field.key]?.trim()))
))

const onSave = async () => {
  if (!props.item || !canSave.value) return
  saving.value = true
  try {
    emit('submit', props.item.requiredHeaders.map((field) => ({
      key: field.key,
      value: values[field.key].trim(),
    })))
  } finally {
    saving.value = false
  }
}
</script>
