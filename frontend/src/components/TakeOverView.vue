<template>
    <div v-if="shouldShow" class="fixed bg-[var(--background-gray-main)] z-50 transition-all w-full h-full inset-0">
        <div class="w-full h-full">
            <VNCViewer 
                :session-id="sessionId"
                :enabled="shouldShow"
                :view-only="false"
                @connected="onVNCConnected"
                @disconnected="onVNCDisconnected"
                @credentials-required="onVNCCredentialsRequired"
            />
        </div>
        <div class="absolute bottom-4 left-1/2 -translate-x-1/2">
            <button @click="exitTakeOver"
                class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring hover:opacity-90 active:opacity-80 bg-[var(--Button-primary-black)] text-[var(--text-onblack)] h-[36px] px-[12px] gap-[6px] text-sm rounded-full border-2 border-[var(--border-dark)] shadow-[0px_8px_32px_0px_rgba(0,0,0,0.32)]">
                <span class="text-sm font-medium text-[var(--text-onblack)]">{{ t('Exit Takeover') }}</span>
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import VNCViewer from './VNCViewer.vue';

const route = useRoute();
const { t } = useI18n();

// Takeover state
const takeOverActive = ref(false);
const currentSessionId = ref('');



// Listen to takeover events
const handleTakeOverEvent = (event: Event) => {
    const customEvent = event as CustomEvent;
    takeOverActive.value = customEvent.detail.active;
    currentSessionId.value = customEvent.detail.sessionId;
};

// VNC event handlers
const onVNCConnected = () => {
    console.log('TakeOver VNC connection successful');
};

const onVNCDisconnected = (reason?: any) => {
    console.log('TakeOver VNC connection disconnected', reason);
};

const onVNCCredentialsRequired = () => {
    console.log('TakeOver VNC credentials required');
};

// Calculate whether to show takeover view
const shouldShow = computed(() => {
    // Check component state first (from takeover event)
    if (takeOverActive.value && currentSessionId.value) {
        return true;
    }
    
    // Also check route parameters (for direct URL access or page refresh)
    const { params: { sessionId }, query: { vnc } } = route;
    // Only show if both sessionId exists in route AND vnc=1 in query
    return !!sessionId && vnc === '1';
});

// Add event listener when component is mounted
onMounted(() => {
    window.addEventListener('takeover', handleTakeOverEvent as EventListener);
});



// Remove event listener when component is unmounted
onBeforeUnmount(() => {
    window.removeEventListener('takeover', handleTakeOverEvent as EventListener);
});

// Get session ID
const sessionId = computed(() => {
    return currentSessionId.value || route.params.sessionId as string || '';
});

// Exit takeover functionality
const exitTakeOver = () => {
    // Update local state
    takeOverActive.value = false;
    currentSessionId.value = '';
};

// Expose sessionId for parent component to use
defineExpose({
    sessionId
});
</script>

<style scoped>
</style>