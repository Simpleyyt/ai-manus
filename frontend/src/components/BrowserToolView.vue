<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]">
    <div class="flex-1 flex items-center justify-center">
      <div class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center">
        {{ toolContent?.args?.url || 'Browser' }}
      </div>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div class="px-0 py-0 flex flex-col relative h-full">
      <div class="w-full h-full object-cover flex items-center justify-center bg-[var(--fill-white)] relative">
        <div class="w-full h-full">
          <div v-if="props.live" ref="vncContainer"
            style="display: flex; width: 100%; height: 100%; overflow: auto; background: rgb(40, 40, 40);">
          </div>
          <img v-else alt="Image Preview" class="cursor-pointer w-full" referrerpolicy="no-referrer" :src="getFileDownloadUrl(toolContent?.content?.screenshot)">
        </div>
        <button
          @click="takeOver"
          class="absolute right-[10px] bottom-[10px] z-10 min-w-10 h-10 flex items-center justify-center rounded-full bg-[var(--background-white-main)] text-[var(--text-primary)] border border-[var(--border-main)] shadow-[0px_5px_16px_0px_var(--shadow-S),0px_0px_1.25px_0px_var(--shadow-S)] backdrop-blur-3xl cursor-pointer hover:bg-[var(--text-brand)] hover:px-4 hover:text-[var(--text-white)] group transition-width duration-300">
          <TakeOverIcon />
          <span
            class="text-sm max-w-0 overflow-hidden whitespace-nowrap opacity-0 transition-all duration-300 group-hover:max-w-[200px] group-hover:opacity-100 group-hover:ml-1 group-hover:text-[var(--text-white)]">{{ t('Take Over') }}</span></button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ToolContent } from '../types/message';
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { getVNCUrl } from '../api/agent';
import { getFileDownloadUrl } from '../api/file';
// @ts-ignore
import RFB from '@novnc/novnc/lib/rfb';
import TakeOverIcon from './icons/TakeOverIcon.vue';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

const { t } = useI18n();
const vncContainer = ref<HTMLDivElement | null>(null);
let rfb: RFB | null = null;

const initVNCConnection = () => {
  if (!vncContainer.value) return;

  if (rfb) {
    rfb.disconnect();
    rfb = null;
  }

  const sessionId = props.sessionId;
  const wsUrl = getVNCUrl(sessionId);

  // Create NoVNC connection
  rfb = new RFB(vncContainer.value, wsUrl, {
    credentials: { password: '' },
    shared: true,
    repeaterID: '',
    wsProtocols: ['binary'],
    // Scaling options
    scaleViewport: true,  // Automatically scale to fit container
    //resizeSession: true   // Request server to adjust resolution
  });

  // Explicitly set viewOnly property
  rfb.viewOnly = true;
  rfb.scaleViewport = true;
  //rfb.resizeSession = true;

  rfb.addEventListener('connect', () => {
    console.log('VNC connection successful');
  });

  rfb.addEventListener('disconnect', (e: any) => {
    console.log('VNC connection disconnected', e);
  });

  rfb.addEventListener('credentialsrequired', () => {
    console.log('VNC credentials required');
  });
};

onMounted(() => {
  initVNCConnection();
});

watch(vncContainer, () => {
  if (vncContainer.value) {
    initVNCConnection();
  }
});

onBeforeUnmount(() => {
  if (rfb) {
    rfb.disconnect();
    rfb = null;
  }
});

const takeOver = () => {
  window.dispatchEvent(new CustomEvent('takeover', {
    detail: {
      sessionId: props.sessionId,
      active: true
    }
  }));
};
</script>
