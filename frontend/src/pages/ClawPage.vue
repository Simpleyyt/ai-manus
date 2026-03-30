<template>
  <SimpleBar ref="simpleBarRef" @scroll="handleScroll">
    <div class="relative flex flex-col h-full flex-1 min-w-0 px-5">

      <!-- Header (only shown when claw exists) -->
      <div
        v-if="hasClaw"
        class="sm:min-w-[390px] flex flex-row items-center justify-between pt-3 pb-1 gap-1 sticky top-0 z-10 bg-[var(--background-gray-main)] flex-shrink-0">
        <div class="flex items-center flex-1">
          <div
            v-if="!isLeftPanelShow"
            class="flex h-7 w-7 items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-gray-main)]"
            @click="toggleLeftPanel"
          >
            <PanelLeft class="size-5 text-[var(--icon-secondary)]" />
          </div>
        </div>
        <div class="max-w-full sm:max-w-[768px] sm:min-w-[390px] flex w-full flex-col gap-[4px] overflow-hidden">
          <div class="text-[var(--text-primary)] text-lg font-medium w-full flex flex-row items-center justify-between flex-1 min-w-0 gap-2">
            <div class="flex flex-row items-center gap-[6px] flex-1 min-w-0">
              <div class="claw-icon-nav w-6 h-6 flex-shrink-0" />
              <span class="whitespace-nowrap text-ellipsis overflow-hidden">Manus Claw</span>
              <span
                v-if="formattedCountdown != null"
                class="ml-1 text-sm font-mono px-1.5 py-0.5 rounded bg-[var(--fill-tsp-white-main)] text-[var(--text-tertiary)] whitespace-nowrap"
              >{{ formattedCountdown }}</span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <button
                @click="handleDeleteClaw"
                class="h-8 px-3 rounded-[100px] inline-flex items-center gap-1 clickable outline outline-1 outline-offset-[-1px] outline-[var(--border-btn-main)] hover:bg-[var(--fill-tsp-white-light)] text-[var(--text-secondary)] text-sm font-medium"
              >
                {{ t('Delete') }}
              </button>
            </div>
          </div>
        </div>
        <div class="flex-1"></div>
      </div>

      <!-- Main content area -->
      <div class="mx-auto w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] flex flex-col flex-1">

        <!-- Create Page (no claw instance) -->
        <div v-if="!hasClaw && !isLoadingClaw" class="flex flex-col flex-1 min-h-0 overflow-y-auto">
          <div class="flex flex-col items-center justify-center flex-1 px-4 py-12 w-full">
            <div class="w-full rounded-2xl overflow-hidden bg-[#ECECEB] dark:bg-[#231a33] aspect-video mb-8 flex flex-col items-center justify-center gap-4 px-4">
              <h1 class="text-2xl sm:text-3xl font-bold tracking-tight"><span class="text-[#c0392b]">OpenClaw</span> <span class="text-[var(--text-tertiary)]">×</span> <span class="text-[#3b82f6]">Manus</span></h1>
              <img :src="openclawColorImage" alt="OpenClaw" class="w-20 h-20 sm:w-24 sm:h-24 object-contain drop-shadow-lg" />
            </div>

            <div class="w-full grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
              <div class="flex flex-col gap-3 p-4 rounded-2xl bg-[var(--fill-tsp-white-main)] border border-[var(--border-main)]">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-[var(--fill-tsp-white-main)] border border-[var(--border-main)] flex items-center justify-center">
                    <Code class="w-4 h-4 text-[var(--text-primary)]" />
                  </div>
                  <h3 class="text-[var(--text-primary)] font-medium text-sm">{{ t('Deploy OpenClaw Instantly') }}</h3>
                </div>
                <p class="text-[var(--text-secondary)] text-xs leading-relaxed">
                  {{ t('OpenClaw is an AI assistant with unique personality and long-term memory, one-click deploy to sandbox cloud, no complex setup, 24/7 online') }}
                </p>
              </div>
              <div class="flex flex-col gap-3 p-4 rounded-2xl bg-[var(--fill-tsp-white-main)] border border-[var(--border-main)]">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-[var(--fill-tsp-white-main)] border border-[var(--border-main)] flex items-center justify-center">
                    <MessageSquarePlus class="w-4 h-4 text-[var(--text-primary)]" />
                  </div>
                  <h3 class="text-[var(--text-primary)] font-medium text-sm">{{ t('Chat Freely via Manus') }}</h3>
                </div>
                <p class="text-[var(--text-secondary)] text-xs leading-relaxed">
                  {{ t('Auto-configured with powerful LLMs and skill libraries, supports multiple chat tools, proactively completes various tasks') }}
                </p>
              </div>
            </div>

            <div class="w-full">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-[var(--text-primary)] font-semibold text-lg">{{ t('Get Started') }}</h2>
              </div>
              <div class="flex flex-col gap-3">
                <div class="flex items-center justify-between p-4 rounded-2xl bg-[var(--fill-tsp-white-main)] border border-[var(--border-main)]">
                  <div class="flex items-center gap-3">
                    <img :src="openclawColorImage" alt="OpenClaw" class="w-10 h-10 rounded-full object-cover flex-shrink-0" />
                    <div>
                      <h4 class="text-[var(--text-primary)] font-medium text-sm">{{ t('Create Manus Claw') }}</h4>
                      <p class="text-[var(--text-tertiary)] text-xs">{{ t('One-click OpenClaw deployment by Manus') }}</p>
                    </div>
                  </div>
                  <button
                    @click="handleCreateClaw"
                    class="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-[var(--text-primary)] text-[var(--background-gray-main)] text-sm font-medium hover:opacity-90 transition-opacity"
                  >
                    {{ t('Create') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading claw state -->
        <div v-else-if="isLoadingClaw" class="flex flex-1 items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <div class="w-8 h-8 border-2 border-[var(--text-tertiary)] border-t-transparent rounded-full animate-spin" />
            <span class="text-[var(--text-tertiary)] text-sm">{{ t('Loading...') }}</span>
          </div>
        </div>

        <!-- Chat Interface (claw exists) -->
        <template v-else>
          <!-- Messages -->
          <div class="flex flex-col w-full gap-[12px] pb-[80px] pt-[12px] flex-1 overflow-y-auto">
            <ChatMessage
              v-for="(msg, index) in messages"
              :key="messageKey(msg, index)"
              :message="msg"
              :hideHeader="isConsecutiveAssistant(messages, index)"
              :assistantIcon="ClawIcon"
              assistantName="Claw"
              :hideAllFilesButton="true"
            />

            <!-- Loading indicator while waiting for response -->
            <LoadingIndicator v-if="isWaitingResponse && !hasStreamingContent" :text="$t('Thinking')" />

          </div>

          <!-- Input Area -->
          <div class="flex flex-col bg-[var(--background-gray-main)] sticky bottom-0">
            <button
              v-if="!follow"
              @click="handleFollow"
              class="flex items-center justify-center w-[36px] h-[36px] rounded-full bg-[var(--background-white-main)] hover:bg-[var(--background-gray-main)] clickable border border-[var(--border-main)] shadow-[0px_5px_16px_0px_var(--shadow-S),0px_0px_1.25px_0px_var(--shadow-S)] absolute -top-20 left-1/2 -translate-x-1/2"
            >
              <ArrowDown class="text-[var(--icon-primary)]" :size="20" />
            </button>
            <ChatBox
              v-model="inputMessage"
              :rows="1"
              :isRunning="false"
              :hideStopButton="true"
              :allowSendFilesOnly="true"
              :attachments="attachments"
              @submit="handleSubmit"
            />
          </div>
        </template>

      </div>
    </div>
  </SimpleBar>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { PanelLeft, Code, MessageSquarePlus, ArrowDown } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import SimpleBar from '../components/SimpleBar.vue';
import ChatBox from '../components/ChatBox.vue';
import ChatMessage from '../components/ChatMessage.vue';
import LoadingIndicator from '../components/ui/LoadingIndicator.vue';
import ClawIcon from '../components/icons/ClawIcon.vue';
import openclawColorImage from '../assets/openclaw-color.png';
import { useLeftPanel } from '../composables/useLeftPanel';
import { useFilePanel } from '../composables/useFilePanel';
import { useDialog } from '../composables/useDialog';
import {
  getClaw, createClaw, deleteClaw,
  getClawHistory, ClawWebSocket,
  type Claw, type ClawStatus, type ClawEvent,
} from '../api/claw';
import { Message, MessageContent, AttachmentsContent, isConsecutiveAssistant } from '../types/message';
import type { FileInfo } from '../api/file';
import { showErrorToast } from '../utils/toast';

const { t } = useI18n();
const { isLeftPanelShow, toggleLeftPanel } = useLeftPanel();
const { hideFilePanel } = useFilePanel();
const { showConfirmDialog } = useDialog();

const simpleBarRef = ref<InstanceType<typeof SimpleBar>>();

const isLoadingClaw = ref(true);
const clawData = ref<Claw | null>(null);
const clawStatus = ref<ClawStatus>('stopped');
const messages = ref<Message[]>([]);
const inputMessage = ref('');
const isWaitingResponse = ref(false);
const follow = ref(true);
const attachments = ref<FileInfo[]>([]);

let clawWS: ClawWebSocket | null = null;
let statusPollingTimer: number | null = null;
let expiryTimer: number | null = null;
const streamingAssistantIdx = ref(-1);
const remainingSeconds = ref<number | null>(null);

const formattedCountdown = computed(() => {
  const s = remainingSeconds.value;
  if (s == null || s < 0) return null;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
});

const startExpiryCountdown = (expiresAt: string) => {
  stopExpiryCountdown();
  const utcExpires = expiresAt.endsWith('Z') || expiresAt.includes('+') ? expiresAt : expiresAt + 'Z';
  const tick = () => {
    const diff = Math.floor((new Date(utcExpires).getTime() - Date.now()) / 1000);
    if (diff <= 0) {
      remainingSeconds.value = 0;
      stopExpiryCountdown();
      handleExpired();
      return;
    }
    remainingSeconds.value = diff;
  };
  tick();
  expiryTimer = window.setInterval(tick, 1000);
};

const stopExpiryCountdown = () => {
  if (expiryTimer) {
    clearInterval(expiryTimer);
    expiryTimer = null;
  }
};

const handleExpired = async () => {
  clawWS?.disconnect();
  clawWS = null;
  isWaitingResponse.value = false;
  streamingAssistantIdx.value = -1;
  stopStatusPolling();
  try { await deleteClaw(); } catch {}
  clawData.value = null;
  clawStatus.value = 'stopped';
  messages.value = [];
  remainingSeconds.value = null;
  isLoadingClaw.value = false;
};

// ------------------------------------------------------------------
// History
// ------------------------------------------------------------------

const loadHistory = async () => {
  try {
    const history = await getClawHistory();
    const loaded: Message[] = [];
    for (const m of history) {
      if (m.role === 'attachments' && m.attachments?.length) {
        const attRole = (m.content === 'user' ? 'user' : 'assistant') as 'user' | 'assistant';
        loaded.push({
          type: 'attachments',
          content: {
            role: attRole,
            attachments: m.attachments.map(a => ({
              file_id: a.file_id,
              filename: a.filename,
              content_type: a.content_type,
              size: a.size,
              upload_date: '',
              file_url: a.file_url,
            })),
            timestamp: m.timestamp,
          } as AttachmentsContent,
        });
      } else {
        let text = m.content || '';
        if (text.startsWith('i18n:')) {
          text = t(text.slice(5));
        }
        loaded.push({
          type: m.role as 'user' | 'assistant',
          content: {
            content: text,
            timestamp: m.timestamp,
          } as MessageContent,
        });
      }
    }
    messages.value = loaded;
  } catch (err) {
    console.error('Failed to load claw history:', err);
  }
};

// ------------------------------------------------------------------
// WebSocket event stream
// ------------------------------------------------------------------

const setupWebSocket = () => {
  clawWS?.disconnect();

  clawWS = new ClawWebSocket({
    onEvent: (event: ClawEvent) => handleWSEvent(event),
  });
};

const handleWSEvent = (chunk: ClawEvent) => {
  if (chunk.type === 'catchup') {
    // Reconnected while a response was in progress
    if (streamingAssistantIdx.value < 0) {
      streamingAssistantIdx.value = messages.value.length;
      messages.value.push({
        type: 'assistant',
        content: { content: '', timestamp: Math.floor(Date.now() / 1000) } as MessageContent,
      });
      isWaitingResponse.value = true;
    }
    if (chunk.content && streamingAssistantIdx.value >= 0) {
      (messages.value[streamingAssistantIdx.value].content as MessageContent).content = chunk.content;
    }
    return;
  }

  if (chunk.type === 'text') {
    if (streamingAssistantIdx.value < 0) {
      streamingAssistantIdx.value = messages.value.length;
      messages.value.push({
        type: 'assistant',
        content: { content: '', timestamp: Math.floor(Date.now() / 1000) } as MessageContent,
      });
    }
    if (chunk.content && streamingAssistantIdx.value >= 0) {
      (messages.value[streamingAssistantIdx.value].content as MessageContent).content += chunk.content;
    }
    return;
  }

  if (chunk.type === 'file' && chunk.file_id) {
    const fileInfo: FileInfo = {
      file_id: chunk.file_id,
      filename: chunk.filename || chunk.file_id,
      content_type: chunk.content_type,
      size: chunk.size ?? 0,
      upload_date: chunk.upload_date || new Date().toISOString(),
      file_url: chunk.file_url,
    };
    messages.value.push({
      type: 'attachments',
      content: {
        role: 'assistant',
        attachments: [fileInfo],
        timestamp: Math.floor(Date.now() / 1000),
      } as AttachmentsContent,
    });
    return;
  }

  if (chunk.type === 'done') {
    streamingAssistantIdx.value = -1;
    isWaitingResponse.value = false;
    return;
  }

  if (chunk.type === 'status') {
    const newStatus = chunk.status!;
    clawStatus.value = newStatus;
    if (newStatus === 'stopped' || newStatus === 'error') {
      streamingAssistantIdx.value = -1;
      isWaitingResponse.value = false;
    }
    return;
  }

  if (chunk.type === 'error') {
    if (streamingAssistantIdx.value >= 0) {
      (messages.value[streamingAssistantIdx.value].content as MessageContent).content
        += `\n⚠️ ${chunk.error || t('An error occurred')}`;
    } else {
      messages.value.push({
        type: 'assistant',
        content: { content: `⚠️ ${chunk.error || t('An error occurred')}`, timestamp: Math.floor(Date.now() / 1000) } as MessageContent,
      });
    }
    streamingAssistantIdx.value = -1;
    isWaitingResponse.value = false;
  }
};

// ------------------------------------------------------------------
// UI helpers
// ------------------------------------------------------------------

const hasClaw = computed(() => clawData.value !== null);

const messageKey = (msg: Message, index: number): string => {
  if (msg.type === 'attachments') {
    const ac = msg.content as AttachmentsContent;
    const ids = ac.attachments?.map(a => a.file_id).join(',') || '';
    return `att-${ac.role}-${ac.timestamp}-${ids}`;
  }
  const mc = msg.content as MessageContent;
  const prefix = (mc.content || '').slice(0, 40);
  return `${msg.type}-${mc.timestamp}-${index}-${prefix}`;
};

const hasStreamingContent = computed(() => {
  if (streamingAssistantIdx.value < 0) return false;
  const msg = messages.value[streamingAssistantIdx.value];
  return msg && (msg.content as MessageContent).content.length > 0;
});

const handleScroll = () => {
  follow.value = simpleBarRef.value?.isScrolledToBottom() ?? false;
};

const handleFollow = () => {
  follow.value = true;
  simpleBarRef.value?.scrollToBottom();
};

watch(messages, async () => {
  await nextTick();
  if (follow.value) {
    simpleBarRef.value?.scrollToBottom();
  }
}, { deep: true });

// ------------------------------------------------------------------
// Claw lifecycle
// ------------------------------------------------------------------

const loadClaw = async () => {
  try {
    isLoadingClaw.value = true;
    const claw = await getClaw();
    clawData.value = claw;
    clawStatus.value = claw.status;

    if (claw.status === 'error' || claw.status === 'stopped') {
      if (claw.status === 'error') {
        showErrorToast(claw.error_message || t('Creation failed, please try again later'));
      }
      await deleteClaw().catch(() => {});
      clawData.value = null;
      isLoadingClaw.value = false;
      return;
    }

    if (claw.status === 'creating') {
      startStatusPolling();
      return;
    }

    await loadHistory();
    if (claw.status === 'running') {
      setupWebSocket();
      if (claw.expires_at) startExpiryCountdown(claw.expires_at);
    }
    isLoadingClaw.value = false;
    await nextTick();
    follow.value = true;
    simpleBarRef.value?.scrollToBottom();
  } catch (err: any) {
    if (err?.code === 404 || err?.code === 40400) {
      clawData.value = null;
    } else {
      console.error('Failed to load claw:', err);
    }
    isLoadingClaw.value = false;
  }
};

const startStatusPolling = () => {
  if (statusPollingTimer) return;
  if (clawStatus.value === 'running') return;

  statusPollingTimer = window.setInterval(async () => {
    try {
      const claw = await getClaw();
      clawData.value = claw;
      clawStatus.value = claw.status;
      if (claw.status === 'running') {
        stopStatusPolling();
        await loadHistory();
        setupWebSocket();
        if (claw.expires_at) startExpiryCountdown(claw.expires_at);
        isLoadingClaw.value = false;
        await nextTick();
        follow.value = true;
        simpleBarRef.value?.scrollToBottom();
      } else if (claw.status === 'error') {
        stopStatusPolling();
        showErrorToast(claw.error_message || t('Creation failed, please try again later'));
        await deleteClaw().catch(() => {});
        clawData.value = null;
        isLoadingClaw.value = false;
      }
    } catch {
      stopStatusPolling();
    }
  }, 3000);
};

const stopStatusPolling = () => {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer);
    statusPollingTimer = null;
  }
};

const handleCreateClaw = async () => {
  isLoadingClaw.value = true;
  try {
    const claw = await createClaw();
    clawData.value = claw;
    clawStatus.value = claw.status;
    if (claw.status === 'running') {
      await loadHistory();
      setupWebSocket();
      if (claw.expires_at) startExpiryCountdown(claw.expires_at);
      isLoadingClaw.value = false;
      await nextTick();
      follow.value = true;
      simpleBarRef.value?.scrollToBottom();
    } else if (claw.status === 'error') {
      showErrorToast(claw.error_message || t('Creation failed, please try again later'));
      await deleteClaw().catch(() => {});
      clawData.value = null;
      isLoadingClaw.value = false;
    } else {
      startStatusPolling();
    }
  } catch (err: any) {
    showErrorToast(err?.message || t('Creation failed, please try again later'));
    await deleteClaw().catch(() => {});
    clawData.value = null;
    isLoadingClaw.value = false;
  }
};

const handleDeleteClaw = () => {
  showConfirmDialog({
    title: t('Are you sure you want to delete Claw?'),
    content: t('Chat history will be cleared. The Claw instance will remain available for re-creation.'),
    confirmText: t('Delete'),
    cancelText: t('Cancel'),
    confirmType: 'danger',
    onConfirm: async () => {
      clawWS?.disconnect();
      clawWS = null;
      isWaitingResponse.value = false;
      streamingAssistantIdx.value = -1;
      stopStatusPolling();
      stopExpiryCountdown();
      try {
        await deleteClaw();
      } catch (err) {
        console.error('Failed to delete claw:', err);
      }
      clawData.value = null;
      clawStatus.value = 'stopped';
      messages.value = [];
      remainingSeconds.value = null;
      isLoadingClaw.value = false;
    },
  });
};

const handleRecreateClaw = async () => {
  isLoadingClaw.value = true;
  stopExpiryCountdown();
  try {
    const claw = await createClaw();
    clawData.value = claw;
    clawStatus.value = claw.status;
    if (claw.status === 'running') {
      await loadHistory();
      setupWebSocket();
      if (claw.expires_at) startExpiryCountdown(claw.expires_at);
      isLoadingClaw.value = false;
      await nextTick();
      follow.value = true;
      simpleBarRef.value?.scrollToBottom();
    } else if (claw.status === 'error') {
      showErrorToast(claw.error_message || t('Creation failed, please try again later'));
      await deleteClaw().catch(() => {});
      clawData.value = null;
      isLoadingClaw.value = false;
    } else {
      startStatusPolling();
    }
  } catch (err: any) {
    showErrorToast(err?.message || t('Creation failed, please try again later'));
    await deleteClaw().catch(() => {});
    clawData.value = null;
    isLoadingClaw.value = false;
  }
};

// ------------------------------------------------------------------
// Send message
// ------------------------------------------------------------------

const handleSubmit = async () => {
  const msg = inputMessage.value.trim();
  const files = attachments.value;
  if (!msg && files.length === 0) return;
  if (isWaitingResponse.value) return;
  if (clawStatus.value !== 'running') {
    return;
  }

  const successFiles = files.filter((f: FileInfo) => !('status' in f) || (f as FileInfo & { status?: string }).status === 'success');
  const msgToSend = msg || (successFiles.length > 0 ? t('Please check {count} attachment(s) I sent', { count: successFiles.length }) : '');

  if (msgToSend) {
    messages.value.push({
      type: 'user',
      content: { content: msgToSend, timestamp: Math.floor(Date.now() / 1000) } as MessageContent,
    });
  }

  if (successFiles.length > 0) {
    messages.value.push({
      type: 'attachments',
      content: {
        role: 'user',
        attachments: successFiles,
        timestamp: Math.floor(Date.now() / 1000),
      } as AttachmentsContent,
    });
    attachments.value.length = 0;
  }

  inputMessage.value = '';
  follow.value = true;
  isWaitingResponse.value = true;

  const fileIds = successFiles.map((f: FileInfo) => f.file_id).filter(Boolean);
  if (clawWS?.isConnected) {
    clawWS.send(msgToSend, 'default', fileIds.length > 0 ? fileIds : undefined);
  } else {
    isWaitingResponse.value = false;
    messages.value.push({
      type: 'assistant',
      content: { content: `⚠️ ${t('WebSocket not connected, please try again later')}`, timestamp: Math.floor(Date.now() / 1000) } as MessageContent,
    });
  }
};

// ------------------------------------------------------------------
// Lifecycle
// ------------------------------------------------------------------

onMounted(() => {
  loadClaw();
});

onUnmounted(() => {
  clawWS?.disconnect();
  stopStatusPolling();
  stopExpiryCountdown();
  hideFilePanel();
});
</script>

<style scoped>
.claw-icon-nav {
  background: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20fill='none'%20viewBox='0%200%2020%2020'%3e%3cpath%20fill='%23111'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024m7.867.197c-.748-.602-3.56-1.662-6.942.985-1.551%201.213-2.034%202.618-2.061%203.874a6.1%206.1%200%200%200%20.805%203.094.75.75%200%200%201-1.29.766q-.05-.09-.103-.188a1%201%200%200%200-.203.182.47.47%200%200%200-.11.22.6.6%200%200%200%20.057.343c.515%201.26%201.491%202.1%202.225%202.285.138.035.262.008.425-.11q.096-.07.188-.167a3%203%200%200%201-.137-.145.75.75%200%200%201%201.136-.98c.294.34%201.034.704%201.948.732.877.027%201.782-.262%202.435-1.037.652-.774.809-1.508.746-2.142-.063-.632-.354-1.218-.711-1.672-.13-.103-.398-.251-.777-.376a4.1%204.1%200%200%200-1.234-.213.75.75%200%200%201%200-1.5c.469%200%20.955.077%201.4.198.017-.29.076-.576.169-.844.297-.856.974-1.644%201.942-1.966.378-.127.492-.348.51-.532.022-.213-.074-.53-.418-.807m2.527%205.25c-.675.81-1.314%201.235-1.947%201.378q-.082.017-.16.027c.093.287.16.591.192.91a4%204%200%200%201-.046%201.116c.299-.098.542-.23.763-.349.79-.428%201.19-1.134%201.336-1.812.073-.341.077-.657.04-.898-.033-.222-.087-.31-.09-.319a.3.3%200%200%200-.067-.046q-.013-.006-.021-.007'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e") no-repeat center;
  background-size: contain;
}

:global(.dark) .claw-icon-nav {
  background-image: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='20'%20height='20'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23fff'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e");
}

.claw-icon-large {
  background: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='64'%20height='64'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23888'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e") no-repeat center;
  background-size: contain;
}

:global(.dark) .claw-icon-large {
  background-image: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='64'%20height='64'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23ccc'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e");
}
</style>
