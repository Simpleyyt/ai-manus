<template>
  <div
    ref="vncContainer"
    class="vnc-container"
    style="display: flex; width: 100%; height: 100%; overflow: auto; background: rgb(40, 40, 40);">
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, watch } from 'vue';
import { getVNCUrl } from '@/api/agent';
// @ts-ignore
import RFB from '@novnc/novnc/lib/rfb';

const props = defineProps<{
  sessionId: string;
  enabled?: boolean;
  viewOnly?: boolean;
}>();

const emit = defineEmits<{
  connected: [];
  disconnected: [reason?: any];
  credentialsRequired: [];
}>();

const vncContainer = ref<HTMLDivElement | null>(null);
let rfb: RFB | null = null;

const initVNCConnection = async () => {
  if (!vncContainer.value || !props.enabled) return;

  // Disconnect existing connection
  if (rfb) {
    rfb.disconnect();
    rfb = null;
  }

  try {
    const wsUrl = await getVNCUrl(props.sessionId);

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

    // Set viewOnly based on props, default to false (interactive)
    rfb.viewOnly = props.viewOnly ?? false;
    rfb.scaleViewport = true;
    //rfb.resizeSession = true;

    rfb.addEventListener('connect', () => {
      console.log('VNC connection successful');
      emit('connected');
    });

    rfb.addEventListener('disconnect', (e: any) => {
      console.log('VNC connection disconnected', e);
      emit('disconnected', e);
    });

    rfb.addEventListener('credentialsrequired', () => {
      console.log('VNC credentials required');
      emit('credentialsRequired');
    });
  } catch (error) {
    console.error('Failed to initialize VNC connection:', error);
  }
};

const disconnect = () => {
  if (rfb) {
    rfb.disconnect();
    rfb = null;
  }
};

// Watch for session ID or enabled state changes
watch([() => props.sessionId, () => props.enabled], () => {
  if (props.enabled && vncContainer.value) {
    initVNCConnection();
  } else {
    disconnect();
  }
}, { immediate: true });

// Watch for container availability
watch(vncContainer, () => {
  if (vncContainer.value && props.enabled) {
    initVNCConnection();
  }
});

onBeforeUnmount(() => {
  disconnect();
});

// Expose methods for parent component
defineExpose({
  disconnect,
  initConnection: initVNCConnection
});
</script>

<style scoped>
</style>
