<template>
  <!--
    Official CopyChatEvent → ChatToolbarItem → IconButton (1to1mfjf57qzz / 635745):
    IconButton: flex h-7 w-7 items-center justify-center cursor-pointer rounded-md
                + gray hover:bg-[var(--fill-tsp-white-light)]
    ChatToolbarItem: size-7 + icon size-[16px] text-[var(--icon-tertiary)]
    Callers merge size-[28px] / size-[32px] rounded-[8px] etc. via buttonClass.
  -->
  <button
    v-if="text.trim()"
    type="button"
    class="flex h-7 w-7 size-7 items-center justify-center cursor-pointer rounded-md border-0 bg-transparent p-0 hover:bg-[var(--fill-tsp-white-light)]"
    :class="buttonClass"
    :title="copied ? t('Copied') : t('Copy')"
    :aria-label="copied ? t('Copied') : t('Copy')"
    @click.stop="handleCopy">
    <Check
      v-if="copied"
      class="size-[16px] text-[var(--icon-tertiary)]"
      :class="iconClass"
      :size="16"
      aria-hidden="true" />
    <Copy
      v-else
      class="size-[16px] text-[var(--icon-tertiary)]"
      :class="iconClass"
      :size="16"
      aria-hidden="true" />
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Check, Copy } from 'lucide-vue-next'
import { copyToClipboard } from '@/utils/dom'

const props = defineProps<{
  text: string
  /** Merged onto IconButton/ChatToolbarItem shell (e.g. size-[28px], size-[32px] rounded-[8px]) */
  buttonClass?: string
  /** Merged onto icon (e.g. size-[18px] on user bubble) */
  iconClass?: string
}>()

const { t } = useI18n()
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

const handleCopy = async () => {
  const ok = await copyToClipboard(props.text)
  if (!ok) return
  copied.value = true
  if (copiedTimer) clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>
