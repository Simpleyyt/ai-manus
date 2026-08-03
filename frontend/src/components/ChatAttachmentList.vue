<template>
  <div
    class="max-w-full overflow-hidden flex flex-col flex-wrap gap-2"
    :class="alignEnd ? 'justify-start items-end' : 'justify-start'"
  >
    <!-- Official user image grid: 6×88px cols, gap 8, right-aligned via column-start -->
    <div
      v-if="imageAttachments.length"
      class="grid gap-[8px] max-w-full grid-cols-[repeat(6,minmax(0,88px))]"
      data-testid="chat-detail-image-grid"
    >
      <div
        v-for="(attachment, index) in imageAttachments"
        :key="attachment.file_id"
        class="aspect-square w-full"
        :style="{ gridColumnStart: imageColStart(index) }"
        @click="showFilePreviewer(attachment)"
      >
        <img
          v-if="previewUrls[attachment.file_id]"
          :src="previewUrls[attachment.file_id]"
          :alt="attachment.filename"
          draggable="false"
          class="max-h-full max-w-full aspect-square w-full object-cover rounded-lg overflow-hidden border border-[var(--border-light)] select-none cursor-pointer"
        />
        <div
          v-else
          class="aspect-square w-full rounded-lg border border-[var(--border-light)] bg-[var(--fill-tsp-white-main)] flex items-center justify-center cursor-pointer"
        >
          <component :is="getFileType(attachment.filename).icon" />
        </div>
      </div>
    </div>

    <!-- Non-image file chips -->
    <div
      v-if="fileAttachments.length"
      class="flex gap-2 flex-wrap max-w-[568px]"
      :class="alignEnd ? 'justify-end' : ''"
    >
      <div
        v-for="attachment in fileAttachments"
        :key="attachment.file_id"
        @click="showFilePreviewer(attachment)"
        class="flex items-center gap-1.5 p-2 pr-2.5 w-[280px] group/attach relative overflow-hidden cursor-pointer rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-menu-white)] hover:bg-[var(--background-tsp-menu-white)]"
        data-testid="chat-detail-file-chip"
      >
        <div class="flex items-center justify-center w-8 h-8 rounded-md">
          <div class="relative flex items-center justify-center">
            <component :is="getFileType(attachment.filename).icon" />
          </div>
        </div>
        <div class="flex flex-col gap-0.5 flex-1 min-w-0">
          <div class="flex-1 min-w-0 flex items-center">
            <div
              class="text-sm text-[var(--text-primary)] text-ellipsis overflow-hidden whitespace-nowrap flex-1 min-w-0"
            >
              {{ attachment.filename }}
            </div>
          </div>
          <div class="text-xs text-[var(--text-tertiary)]">
            {{ getFileTypeText(attachment.filename) }} · {{ formatFileSize(attachment.size) }}
          </div>
        </div>
        <div
          class="items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md w-6 h-6 border border-[var(--border-main)] flex opacity-0 group-hover/attach:opacity-100"
        >
          <Eye class="size-5 w-4 h-4 text-[var(--icon-secondary)]" />
        </div>
      </div>
      <button
        v-if="showAllFilesButton"
        type="button"
        @click="emit('showAllFiles')"
        class="h-[54px] pl-4 pr-1.5 flex items-center justify-center gap-1.5 w-[280px] rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-menu-white)] hover:bg-[var(--background-tsp-menu-white)]"
      >
        <FileSearch :size="16" />
        <span class="text-sm text-[var(--icon-secondary)]">{{ t('View all files in this task') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { Eye, FileSearch } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import type { FileInfo } from '../api/file'
import { getFileDownloadUrl } from '../api/file'
import { formatFileSize, getFileType, getFileTypeText, isImageFile } from '../utils/fileType'
import { useFilePreviewer } from '../composables/useFilePreviewer'

const props = withDefaults(
  defineProps<{
    attachments: FileInfo[]
    alignEnd?: boolean
    showAllFilesButton?: boolean
  }>(),
  {
    alignEnd: false,
    showAllFilesButton: false,
  },
)

const emit = defineEmits<{
  (e: 'showAllFiles'): void
}>()

const { t } = useI18n()
const { showFilePreviewer } = useFilePreviewer()

const imageAttachments = computed(() =>
  props.attachments.filter((a) => isImageFile(a.filename, a.content_type)),
)

const fileAttachments = computed(() =>
  props.attachments.filter((a) => !isImageFile(a.filename, a.content_type)),
)

/** Official: single image uses grid-column-start: 6 (right edge of 6-col grid). */
const imageColStart = (index: number) => {
  const total = imageAttachments.value.length
  return Math.max(1, 7 - total + index)
}

const previewUrls = reactive<Record<string, string>>({})

const resolvePreviews = async () => {
  for (const a of imageAttachments.value) {
    if (previewUrls[a.file_id]) continue
    // Prefer existing previewUrl from optimistic upload (ExtendedFileInfo)
    const existing = (a as FileInfo & { previewUrl?: string }).previewUrl
    if (existing) {
      previewUrls[a.file_id] = existing
      continue
    }
    try {
      previewUrls[a.file_id] = await getFileDownloadUrl(a)
    } catch (e) {
      console.error('Failed to load attachment preview', e)
    }
  }
}

watch(
  () => props.attachments.map((a) => a.file_id).join(','),
  () => {
    void resolvePreviews()
  },
  { immediate: true },
)
</script>
