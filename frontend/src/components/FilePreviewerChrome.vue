<template>
  <!-- Official FilePreviewerHeader: null for image/svg -->
  <div
    v-if="!isImage"
    class="flex h-[56px] shrink-0 items-center justify-between gap-[16px] px-[16px] py-[12px] border-b border-[var(--border-main)]">
    <!-- Official FilePreviewerBrief -->
    <div class="flex min-w-0 flex-1 items-center justify-between">
      <div
        class="flex min-w-0 flex-row items-center gap-[8px] truncate text-[var(--text-secondary)] [&_svg]:flex-shrink-0">
        <a
          href=""
          class="flex size-[36px] flex-shrink-0 items-center justify-center cursor-default"
          target="_blank"
          rel="noreferrer"
          @click.prevent>
          <div class="relative flex items-center justify-center">
            <component :is="fileType.icon" />
          </div>
        </a>
        <div class="flex min-w-0 flex-col truncate text-[var(--text-primary)]">
          <span
            class="truncate text-[14px] font-medium leading-[20px] tracking-[-0.15px]"
            :title="fileInfo.filename">
            {{ fileInfo.filename }}
          </span>
        </div>
      </div>
    </div>

    <div class="flex shrink-0 items-center justify-end gap-[4px] select-none">
      <!-- Official: ToolShare (skip) + ToolDownload -->
      <div class="flex items-center gap-[4px]">
        <div
          class="flex size-[32px] cursor-pointer items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-main)]"
          :title="t('Download')"
          @click="emit('download')">
          <Download class="size-[18px] text-[var(--icon-secondary)]" />
        </div>
      </div>

      <!-- Official: ToolMore (skip) + divider + ToolViewModeMenu + Close -->
      <div class="flex items-center gap-[4px]">
        <div
          v-if="viewMode !== 'fullscreen'"
          class="flex h-[32px] items-center px-[4px]">
          <div class="h-[16px] w-px bg-[var(--border-dark)]" />
        </div>
        <ToolViewModeMenu />
        <div
          class="flex size-[32px] cursor-pointer items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-main)]"
          :title="t('Close')"
          @click="emit('close')">
          <X class="size-[18px] text-[var(--icon-secondary)]" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Download, X } from 'lucide-vue-next'
import type { FileInfo } from '../api/file'
import type { FileType } from '../utils/fileType'
import type { FilePreviewViewMode } from '../composables/useFilePreviewer'
import ToolViewModeMenu from './ToolViewModeMenu.vue'

defineProps<{
  fileInfo: FileInfo
  fileType: FileType
  isImage: boolean
  viewMode: FilePreviewViewMode
}>()

const emit = defineEmits<{
  (e: 'download'): void
  (e: 'close'): void
}>()

const { t } = useI18n()
</script>
