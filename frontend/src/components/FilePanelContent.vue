<template>
      <div class="bg-[var(--background-gray-main)] overflow-hidden shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)] ltr:border-l rtl:border-r border-black/8 dark:border-[var(--border-light)] flex flex-col h-full w-full">
        <div
          class="px-4 pt-2 pb-4 gap-4 flex items-center justify-between flex-shrink-0 border-b border-[var(--border-main)] flex-col-reverse md:flex-row md:py-4">
          <div class="flex justify-between self-stretch flex-1 truncate">
            <div
              class="flex flex-row gap-1 items-center text-[var(--text-secondary)] font-medium truncate [&amp;_svg]:flex-shrink-0">
              <a href="" class="p-1 flex-shrink-0 cursor-default" target="_blank">
                <div class="relative flex items-center justify-center">
                  <component :is="fileType.icon" />
                </div>
              </a>
              <div class="truncate flex flex-col"><span class="truncate" :title="file.filename">{{ file.filename }}</span></div>
            </div>
          </div>
          <div class="flex items-center justify-between gap-2 w-full py-3 md:w-auto md:py-0 select-none">
            <div class="flex items-center gap-2">
              <div @click="download"
                class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
                aria-expanded="false" aria-haspopup="dialog">
                <Download class="text-[var(--icon-secondary)] size-[18px]" />
              </div>
            </div>
            <div class="flex items-center gap-2">
              <div @click="hide"
                class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md">
                <X class="size-5 text-[var(--icon-secondary)]" />
              </div>
            </div>
          </div>
        </div>
        <component :is="fileType.preview" :file="file" />
      </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Download, X } from 'lucide-vue-next';
import type { FileInfo } from '../api/file';
import { getFileDownloadUrl } from '../api/file';
import { getFileType } from '../utils/fileType';

const props = defineProps<{
  file: FileInfo;
}>();

const emit = defineEmits<{
  (e: 'hide'): void
}>();

const hide = () => {
  emit('hide');
};

const fileType = computed(() => {
  return getFileType(props.file.filename);
});

const download = async () => {
  const url = await getFileDownloadUrl(props.file);
  window.open(url, '_blank');
};
</script>
