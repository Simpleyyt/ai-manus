<template>
    <div class="flex flex-col items-center justify-center gap-6 flex-1 w-full min-h-0">
        <div class="flex items-center gap-1.5 rounded-[10px] bg-[var(--fill-tsp-gray-main)] px-2 py-2 w-[280px]">
            <div class="relative flex items-center justify-center">
                <component :is="fileType.icon" />
            </div>
            <div class="flex flex-col gap-0.5 flex-1 min-w-0">
                <div class="text-sm text-[var(--text-primary)] truncate">{{ file.filename }}</div>
                <div class="text-xs text-[var(--text-tertiary)] truncate">{{ getFileTypeText(file.filename) }}</div>
            </div>
        </div>
        <div class="text-sm text-center text-[var(--text-tertiary)]">{{ t('This format cannot be previewed') }}。<br>{{
            t('Please download the file to view its content') }}。
        </div>
        <button @click="download"
            class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring hover:opacity-90 active:opacity-80 bg-[var(--Button-primary-black)] text-[var(--text-onblack)] h-[36px] px-[12px] rounded-[10px] gap-[6px] text-sm">
            <Download :size="16" />
            <span class="text-sm ">{{ t('Download') }}</span>
        </button>
    </div>
</template>

<script setup lang="ts">
import { Download } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';
import type { FileInfo } from '../../api/file';
import { getFileDownloadUrl } from '../../api/file';
import { getFileType, getFileTypeText } from '../../utils/fileType';

const { t } = useI18n();

const props = defineProps<{
    file: FileInfo;
}>();

const fileType = computed(() => {
  return getFileType(props.file.filename);
});

const download = async () => {
  const url = await getFileDownloadUrl(props.file);
  window.open(url, '_blank');
};
</script>