<template>
  <!-- User messages (right-aligned) -->
  <div v-if="content.role === 'user'" class="flex flex-col flex-wrap gap-2 items-end justify-end">
    <div class="flex gap-2 flex-wrap max-w-[568px] justify-end">
      <div v-for="attachment in content.attachments" @click="showFilePanel(attachment)"
        class="flex items-center gap-1.5 p-2 pr-2.5 w-[280px] group/attach relative overflow-hidden cursor-pointer rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-menu-white)] hover:bg-[--background-tsp-menu-white]">
        <div class="flex items-center justify-center w-8 h-8 rounded-md">
          <div class="relative flex items-center justify-center">
            <component :is="getFileType(attachment.filename).icon" />
          </div>
        </div>
        <div class="flex flex-col gap-0.5 flex-1 min-w-0">
          <div class="flex-1 min-w-0 flex items-center">
            <div
              class="text-sm text-[var(--text-primary)] text-ellipsis overflow-hidden whitespace-nowrap flex-1 min-w-0">
              {{ attachment.filename }}</div>
          </div>
          <div class="text-xs text-[var(--text-tertiary)]">{{ getFileTypeText(attachment.filename) }} · {{
            formatFileSize(attachment.size) }}</div>
        </div>
        <div
          class="items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md w-6 h-6 border border-[var(--border-main)] flex opacity-0 group-hover/attach:opacity-100">
          <Eye class="size-5 w-4 h-4 text-[var(--icon-secondary)]" />
        </div>
      </div>
    </div>
  </div>

  <!-- Assistant messages (left-aligned) -->
  <div v-else class="flex flex-col flex-wrap gap-2 justify-start">
    <div class="flex gap-2 flex-wrap max-w-[568px]">
      <div v-for="attachment in content.attachments" @click="showFilePanel(attachment)"
        class="flex items-center gap-1.5 p-2 pr-2.5 w-[280px] group/attach relative overflow-hidden cursor-pointer rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-menu-white)] hover:bg-[--background-tsp-menu-white]">
        <div class="flex items-center justify-center w-8 h-8 rounded-md">
          <div class="relative flex items-center justify-center">
            <component :is="getFileType(attachment.filename).icon" />
          </div>
        </div>
        <div class="flex flex-col gap-0.5 flex-1 min-w-0">
          <div class="flex-1 min-w-0 flex items-center">
            <div
              class="text-sm text-[var(--text-primary)] text-ellipsis overflow-hidden whitespace-nowrap flex-1 min-w-0">
              {{ attachment.filename }}</div>
          </div>
          <div class="text-xs text-[var(--text-tertiary)]">{{ getFileTypeText(attachment.filename) }} · {{
            formatFileSize(attachment.size) }}</div>
        </div>
        <div
          class="items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md w-6 h-6 border border-[var(--border-main)] flex opacity-0 group-hover/attach:opacity-100">
          <Eye class="size-5 w-4 h-4 text-[var(--icon-secondary)]" />
        </div>
      </div>
      <button @click="showAllFiles"
        class="h-[54px] pl-4 pr-1.5 flex items-center justify-center gap-1.5 w-[280px] rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-menu-white)] hover:bg-[var(--background-tsp-menu-white)]">
        <FileSearch :size="16" />
        <span class="text-sm text-[var(--icon-secondary)]">{{ t('View all files in this task') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileSearch, Eye } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import type { AttachmentsContent } from '../types/message';
import { formatFileSize, getFileTypeText } from '../utils/fileType';
import { getFileType } from '../utils/fileType';
import { useSessionFileList } from '../composables/useSessionFileList';
import { useFilePanel } from '../composables/useFilePanel';

const { t } = useI18n();
const { showFilePanel } = useFilePanel();
const { showSessionFileList } = useSessionFileList();

defineProps<{
  content: AttachmentsContent;
}>();

const showAllFiles = () => {
  showSessionFileList();
};

</script>