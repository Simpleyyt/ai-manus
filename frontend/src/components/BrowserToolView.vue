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
          <div ref="vncContainer" style="display: flex; width: 100%; height: 100%; overflow: auto; background: rgb(40, 40, 40);"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ToolContent } from '../types/message';
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { getVNCUrl } from '../api/agent';
// @ts-ignore
import RFB from '@novnc/novnc/lib/rfb';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

const vncContainer = ref<HTMLDivElement | null>(null);
let rfb: RFB | null = null;

onMounted(() => {
  if (!vncContainer.value) return;

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
});

onBeforeUnmount(() => {
  if (rfb) {
    rfb.disconnect();
    rfb = null;
  }
});
</script>
