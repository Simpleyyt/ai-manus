<template>
  <div
    :class="{
      'h-full w-full top-0 ltr:right-0 rtl:left-0 z-50 fixed sm:sticky sm:top-0 sm:right-0 sm:h-[100vh] sm:ml-3 sm:py-3 sm:mr-4': isShow && panelType === 'tool',
      'h-full w-full top-0 ltr:right-0 rtl:left-0 z-50 fixed sm:sticky sm:top-0 sm:h-[100vh]': isShow && panelType === 'file',
      'h-full overflow-hidden': !isShow 
    }"
    :style="{ 'width': isShow ? `${size}px` : '0px', 'opacity': isShow ? '1' : '0', 'transition': '0.2s ease-in-out' }">
    <div class="h-full" :style="{ 'width': isShow ? '100%' : '0px' }">
      <ToolPanelContent v-if="isShow && panelType === 'tool' && toolContent" :sessionId="sessionId" :realTime="realTime" :toolContent="toolContent" :live="live" @hide="hide" @jumpToRealTime="jumpToRealTime" />
      <FilePanelContent v-if="isShow && panelType === 'file' && fileInfo" :file="fileInfo" @hide="hide" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import type { ToolContent } from '../types/message';
import type { FileInfo } from '../api/file';
import { eventBus } from '../utils/eventBus';
import { EVENT_FILE_SHOW } from '../constants/event';
import ToolPanelContent from './ToolPanelContent.vue';
import FilePanelContent from './FilePanelContent.vue';

const isShow = ref(false);
const live = ref(false);
const toolContent = ref<ToolContent>();
const fileInfo = ref<FileInfo>();
const panelType = ref<'tool' | 'file'>('tool');

const emit = defineEmits<{
  (e: 'jumpToRealTime'): void
}>();

defineProps<{
  sessionId?: string;
  realTime: boolean;
  size: number;
}>();

const showTool = (content: ToolContent, isLive: boolean = false) => {
  panelType.value = 'tool';
  toolContent.value = content;
  isShow.value = true;
  live.value = isLive;
}

const showFile = (file: FileInfo) => {
  panelType.value = 'file';
  fileInfo.value = file;
  isShow.value = true;
}

const hide = () => {
  isShow.value = false;
};

const jumpToRealTime = () => {
  emit('jumpToRealTime');
};

onMounted(() => {
  eventBus.on(EVENT_FILE_SHOW, (event: unknown) => {
    const data = event as { file: FileInfo };
    if (data.file) {
      showFile(data.file);
    }
  });
});

onUnmounted(() => {
  eventBus.off(EVENT_FILE_SHOW);
});

defineExpose({
  showTool,
  showFile,
  hide,
  isShow
});
</script>
