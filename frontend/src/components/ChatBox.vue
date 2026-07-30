<template>
  <div class="pb-3 relative bg-[var(--background-gray-main)]">
    <div
      class="flex flex-col rounded-[22px] relative bg-[var(--background-menu-white)] py-3 w-full z-[2] gap-3 shadow-[0px_12px_32px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-main)] focus-within:border focus-within:border-black/20 focus-within:dark:border-[var(--border-dark)]"
    >
      <ChatBoxFiles ref="chatBoxFileListRef" :attachments="attachments"
        @update:attachments="emit('update:attachments', $event)" />
      <div
        class="chat-input-editor overflow-auto ps-4 pe-2 bg-transparent pt-[1px] border-0 focus-visible:ring-0 focus-visible:ring-offset-0 w-full placeholder:text-[var(--text-disable)] text-[15px] leading-[24px] max-h-[216px]"
        :class="dense ? 'min-h-[28px]' : 'min-h-[50px]'"
      >
        <EditorContent :editor="editor" />
      </div>
      <div class="flex gap-1.5 px-3 items-center">
        <div class="relative" ref="plusMenuRef">
          <button type="button" @click="showPlusMenu = !showPlusMenu"
            class="rounded-full border border-[var(--border-main)] inline-flex items-center justify-center gap-1 clickable cursor-pointer text-xs text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-light)] w-8 h-8 p-0"
            :title="t('Add files and more')"
            aria-expanded="false" aria-haspopup="dialog">
            <Plus :size="17" />
          </button>
          <div v-if="showPlusMenu"
            class="absolute bottom-[calc(100%+8px)] left-0 z-50 min-w-[200px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] py-1">
            <button type="button"
              class="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
              @click="handleAddLocalFiles">
              <Paperclip :size="16" class="text-[var(--icon-tertiary)]" />
              {{ t('Add local files') }}
            </button>
          </div>
        </div>
        <div class="flex gap-1.5 ml-auto items-center">
          <button v-if="!isRunning || sendEnabled || hideStopButton"
            class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors text-sm rounded-full p-0 w-8 h-8 min-w-0 hover:opacity-90"
            :class="!sendEnabled ? 'cursor-not-allowed bg-[var(--fill-tsp-white-dark)] hover:opacity-100' : 'cursor-pointer bg-[var(--Button-primary-black)]'"
            @click="handleSubmit">
            <SendIcon :disabled="!sendEnabled" />
          </button>
          <button v-else-if="!hideStopButton" @click="handleStop"
            class="inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-colors bg-[var(--Button-primary-black)] text-[var(--text-onblack)] gap-[4px] hover:opacity-90 rounded-full p-0 w-8 h-8">
            <div class="w-[10px] h-[10px] bg-[var(--icon-onblack)] rounded-[2px]">
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import SendIcon from './icons/SendIcon.vue'
import { useI18n } from 'vue-i18n'
import ChatBoxFiles from './ChatBoxFiles.vue'
import { Paperclip, Plus } from 'lucide-vue-next'
import type { FileInfo } from '../api/file'

const { t } = useI18n()
const hasTextInput = ref(false)
const chatBoxFileListRef = ref()
const showPlusMenu = ref(false)
const plusMenuRef = ref<HTMLElement | null>(null)

const props = withDefaults(defineProps<{
  modelValue: string
  rows: number
  isRunning: boolean
  attachments: FileInfo[]
  hideStopButton?: boolean
  allowSendFilesOnly?: boolean
  /** Manus session detail uses "Send message to Manus"; home keeps the task prompt. */
  placeholder?: string
  dense?: boolean
}>(), {
  placeholder: undefined,
  dense: false,
  hideStopButton: false,
  allowSendFilesOnly: false,
})

const placeholderText = computed(() => props.placeholder || t('Assign a task or type / to see more'))

const sendEnabled = computed(() => {
  const hasFiles = (props.attachments?.length ?? 0) > 0
  const allUploaded = chatBoxFileListRef.value?.isAllUploaded ?? true
  if (props.allowSendFilesOnly) {
    return hasTextInput.value || (hasFiles && allUploaded)
  }
  return hasTextInput.value && (!hasFiles || allUploaded)
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:attachments', value: FileInfo[]): void
  (e: 'submit'): void
  (e: 'stop'): void
}>()

const handleSubmit = () => {
  if (!sendEnabled.value) return
  emit('submit')
}

const handleStop = () => {
  emit('stop')
}

/** Plain-text → TipTap JSON doc (avoids HTML parse of `<`/`&`). */
const plainTextToDoc = (text: string) => ({
  type: 'doc' as const,
  content: (text || '').split('\n').map((line) => ({
    type: 'paragraph' as const,
    ...(line
      ? { content: [{ type: 'text' as const, text: line }] }
      : {}),
  })),
})

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: false,
      codeBlock: false,
      blockquote: false,
      horizontalRule: false,
      // keep bold/italic/lists/hardBreak
    }),
    Placeholder.configure({ placeholder: () => placeholderText.value }),
  ],
  content: plainTextToDoc(props.modelValue || ''),
  editorProps: {
    attributes: { class: 'tiptap ProseMirror focus:outline-none' },
    handleKeyDown: (_view, event) => {
      if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
        if (sendEnabled.value) {
          event.preventDefault()
          handleSubmit()
          return true
        }
      }
      return false
    },
  },
  onUpdate: ({ editor: ed }) => {
    const text = ed.getText({ blockSeparator: '\n' })
    hasTextInput.value = !!text.trim()
    emit('update:modelValue', text)
  },
})

const syncModelToEditor = (val: string) => {
  if (!editor.value) return
  const current = editor.value.getText({ blockSeparator: '\n' })
  if (val !== current) {
    editor.value.commands.setContent(plainTextToDoc(val), { emitUpdate: false })
  }
  hasTextInput.value = !!(val ?? '').trim()
}

watch(() => props.modelValue, (val) => {
  syncModelToEditor(val ?? '')
})

// Retry inbound sync once the editor becomes ready (missed early modelValue).
watch(editor, (ed) => {
  if (ed) syncModelToEditor(props.modelValue ?? '')
})

watch(placeholderText, () => {
  // Placeholder extension reads function; force view update if needed
  if (editor.value?.view) {
    editor.value.view.dispatch(editor.value.state.tr)
  }
})

onBeforeUnmount(() => editor.value?.destroy())

defineExpose({ editor })

const uploadFile = () => {
  chatBoxFileListRef.value?.uploadFile()
}

const handleAddLocalFiles = () => {
  showPlusMenu.value = false
  uploadFile()
}

const onDocClick = (e: MouseEvent) => {
  if (showPlusMenu.value && plusMenuRef.value && !plusMenuRef.value.contains(e.target as Node)) {
    showPlusMenu.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onDocClick))
onUnmounted(() => document.removeEventListener('mousedown', onDocClick))

// Sync initial hasTextInput from modelValue
hasTextInput.value = !!props.modelValue.trim()
</script>

<style>
.chat-input-editor .tiptap {
  outline: none;
  min-height: inherit;
}

.chat-input-editor .tiptap p.is-editor-empty:first-child::before,
.chat-input-editor .tiptap p.is-empty:first-child::before {
  color: var(--text-disable);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
