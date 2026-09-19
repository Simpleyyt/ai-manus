<template>
  <Dialog v-model:open="open">
    <DialogContent class="w-[480px] max-w-[98%] overflow-hidden bg-[var(--background-gray-main)] p-0">
      <DialogHeader class="pt-5 px-5 pb-[10px] pe-8">
        <DialogTitle class="flex items-center gap-1">
          {{ t('Add MCP by URL') }}
          <span
            class="shrink-0 h-[18px] flex items-center justify-center px-1.5 py-1 border border-[var(--border-dark)] rounded-ss-[8px] rounded-se-[10px] rounded-ee-[10px] text-[12px] font-medium text-[var(--text-tertiary)]"
          >
            {{ t('Beta') }}
          </span>
        </DialogTitle>
      </DialogHeader>
      <div class="space-y-6 px-5 pb-5" data-testid="mcp-by-url-dialog">
        <div class="space-y-4">
          <div class="space-y-2">
            <label class="flex items-center gap-1 text-[14px] font-medium text-[var(--text-primary)]">
              {{ t('Server URL') }}
              <span class="text-[13px] text-[var(--function-error)]">*</span>
            </label>
            <input
              v-model="url"
              type="text"
              data-testid="mcp-url-input"
              :placeholder="t('e.g. http://10.0.1.24:8081/mcp')"
              class="flex px-4 py-2 items-center rounded-[10px] bg-[var(--fill-tsp-white-main)] w-full h-[36px] border-none text-[14px] leading-[22px] text-[var(--text-primary)] outline-none focus:ring-[1.5px] focus:ring-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
            >
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-3 p-5">
        <button
          type="button"
          class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg bg-[var(--Button-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-40"
          :disabled="saving || !url.trim()"
          data-testid="mcp-url-save"
          @click="onSave"
        >
          {{ t('Save') }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { createMcpFromUrl, connectorErrorMessage } from '@/composables/connectorsStore'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ created: [] }>()
const { t } = useI18n()
const url = ref('')
const saving = ref(false)

watch(open, (isOpen) => {
  if (isOpen) url.value = ''
})

const onSave = async () => {
  saving.value = true
  try {
    await createMcpFromUrl(url.value.trim())
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
