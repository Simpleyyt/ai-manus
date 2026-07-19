<template>
  <SimpleBar ref="simpleBarRef" @scroll="handleScroll">
    <div ref="chatContainerRef" class="relative flex flex-col h-full flex-1 min-w-0 px-5">
      <div ref="observerRef"
        class="sm:min-w-[390px] flex flex-row items-center justify-between pt-3 pb-1 gap-1 sticky top-0 z-10 bg-[var(--background-gray-main)] flex-shrink-0">
        <div class="flex items-center flex-1"></div>
        <div class="max-w-full sm:max-w-[768px] sm:min-w-[390px] flex w-full flex-col gap-[4px] overflow-hidden">
          <div
            class="text-[var(--text-primary)] text-lg font-medium w-full flex flex-row items-center justify-between flex-1 min-w-0 gap-2">
            <div class="flex flex-row items-center gap-[6px] flex-1 min-w-0">
              <div class="relative shrink-0" ref="modeMenuRef">
                <button type="button"
                  class="inline-flex items-center gap-1 rounded-[8px] px-2 py-1 hover:bg-[var(--fill-tsp-white-main)] text-[var(--text-primary)] text-[15px] font-medium"
                  @click="showModeMenu = !showModeMenu">
                  Manus
                  <span class="text-[12px] text-[var(--text-tertiary)] font-normal">{{ taskMode === 'agent' ? t('Agent mode') : t('Chat mode') }}</span>
                  <ChevronDown :size="14" class="text-[var(--icon-tertiary)]" />
                </button>
                <div v-if="showModeMenu"
                  class="absolute left-0 top-[calc(100%+6px)] z-50 min-w-[220px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] py-1">
                  <button type="button" class="flex w-full flex-col items-start px-3 py-2 hover:bg-[var(--fill-tsp-white-main)]" @click="setTaskMode('agent')">
                    <span class="text-sm font-medium text-[var(--text-primary)]">{{ t('Agent mode') }}</span>
                    <span class="text-[12px] text-[var(--text-tertiary)]">{{ t('Autonomous planning and tool use') }}</span>
                  </button>
                  <button type="button" class="flex w-full flex-col items-start px-3 py-2 hover:bg-[var(--fill-tsp-white-main)]" @click="setTaskMode('chat')">
                    <span class="text-sm font-medium text-[var(--text-primary)]">{{ t('Chat mode') }}</span>
                    <span class="text-[12px] text-[var(--text-tertiary)]">{{ t('Fast answers and discussion') }}</span>
                  </button>
                </div>
              </div>
              <span class="whitespace-nowrap text-ellipsis overflow-hidden text-[var(--text-secondary)] text-[14px] font-normal">
                {{ title }}
              </span>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <!-- Share popover (structure from manus SharePermission UI) -->
              <span class="relative flex-shrink-0" aria-expanded="false" aria-haspopup="dialog">
                <Popover>
                  <PopoverTrigger>
                    <button
                      class="h-8 px-3 rounded-[100px] inline-flex items-center gap-1 clickable outline outline-1 outline-offset-[-1px] outline-[var(--border-btn-main)] hover:bg-[var(--fill-tsp-white-light)]">
                      <ShareIcon color="var(--icon-secondary)" />
                      <span class="text-[var(--text-secondary)] text-sm font-medium">{{ t('Share') }}</span>
                    </button>
                  </PopoverTrigger>
                  <PopoverContent>
                    <div
                      class="w-[400px] flex flex-col rounded-2xl bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S),0px_0px_0px_1px_var(--border-light)]"
                      style="max-width: calc(-16px + 100vw);">
                      <div class="flex flex-col pt-[12px] px-[16px] pb-[16px]">
                        <div class="flex items-center justify-between mb-2 px-[8px]">
                          <div class="text-[15px] font-semibold text-[var(--text-primary)]">{{ t('Share') }}</div>
                        </div>
                        <!-- Only me -->
                        <div @click="handleShareModeChange('private')"
                          :class="{'pointer-events-none opacity-50': sharingLoading}"
                          class="flex items-center gap-[10px] px-[8px] -mx-[8px] py-[8px] rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-main)]">
                          <div
                            :class="shareMode === 'private' ? 'bg-[var(--Button-primary-black)]' : 'bg-[var(--fill-tsp-white-dark)]'"
                            class="size-8 rounded-[8px] flex items-center justify-center">
                            <Lock :size="16" :stroke="shareMode === 'private' ? 'var(--text-onblack)' : 'var(--icon-primary)'" :stroke-width="2" />
                          </div>
                          <div class="flex flex-col flex-1 min-w-0">
                            <div class="text-sm font-medium text-[var(--text-primary)]">{{ t('Only me') }}</div>
                            <div class="text-[13px] text-[var(--text-tertiary)]">{{ t('Only visible to you') }}</div>
                          </div>
                          <Check :size="20" :class="shareMode === 'private' ? 'ml-auto' : 'ml-auto invisible'" :color="shareMode === 'private' ? 'var(--icon-primary)' : 'var(--icon-tertiary)'" />
                        </div>
                        <!-- Public access -->
                        <div @click="handleShareModeChange('public')"
                          :class="{'pointer-events-none opacity-50': sharingLoading}"
                          class="flex items-center gap-[10px] px-[8px] -mx-[8px] py-[8px] rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-main)]">
                          <div
                            :class="shareMode === 'public' ? 'bg-[var(--Button-primary-black)]' : 'bg-[var(--fill-tsp-white-dark)]'"
                            class="size-8 rounded-[8px] flex items-center justify-center">
                            <Globe :size="16" :stroke="shareMode === 'public' ? 'var(--text-onblack)' : 'var(--icon-primary)'" :stroke-width="2" />
                          </div>
                          <div class="flex flex-col flex-1 min-w-0">
                            <div class="text-sm font-medium text-[var(--text-primary)]">{{ t('Public access') }}</div>
                            <div class="text-[13px] text-[var(--text-tertiary)]">{{ t('Anyone with a link can view') }}</div>
                          </div>
                          <Check :size="20" :class="shareMode === 'public' ? 'ml-auto' : 'ml-auto invisible'" :color="shareMode === 'public' ? 'var(--icon-primary)' : 'var(--icon-tertiary)'" />
                        </div>
                        <div class="border-t border-[var(--border-main)] mt-[4px]"></div>

                        <div v-if="shareMode === 'private'">
                          <button @click.stop="handleInstantShare"
                            :disabled="sharingLoading"
                            class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 bg-[var(--Button-primary-black)] text-[var(--text-onblack)] h-[36px] px-[12px] rounded-[10px] gap-[6px] text-sm min-w-16 mt-[16px] w-full disabled:opacity-50 disabled:cursor-not-allowed"
                            tabindex="-1">
                            <div v-if="sharingLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <Link v-else :size="16" stroke="currentColor" :stroke-width="2" />
                            {{ sharingLoading ? t('Sharing...') : t('Share Instantly') }}
                          </button>
                        </div>
                        <div v-else class="mt-[16px] flex flex-col gap-3">
                          <!-- SocialMediaShare row from Manus -->
                          <div class="flex items-center justify-center gap-2">
                            <button type="button" class="size-9 rounded-full border border-[var(--border-main)] flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)]" :title="'X'" @click="shareToSocial('x')">
                              <span class="text-sm font-bold text-[var(--text-primary)]">𝕏</span>
                            </button>
                            <button type="button" class="size-9 rounded-full border border-[var(--border-main)] flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)] text-[12px] font-semibold text-[var(--text-primary)]" @click="shareToSocial('linkedin')">in</button>
                            <button type="button" class="size-9 rounded-full border border-[var(--border-main)] flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)] text-[12px] font-semibold text-[var(--text-primary)]" @click="shareToSocial('facebook')">f</button>
                            <button type="button" class="size-9 rounded-full border border-[var(--border-main)] flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)] text-[11px] font-semibold text-[var(--text-primary)]" @click="shareToSocial('reddit')">r/</button>
                          </div>
                          <button @click.stop="handleCopyLink"
                            :class="linkCopied ? 'inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors active:opacity-80 bg-[var(--Button-primary-white)] text-[var(--text-primary)] hover:opacity-70 h-[36px] px-[12px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full border border-[var(--border-btn-main)] shadow-none' : 'inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 bg-[var(--Button-primary-black)] text-[var(--text-onblack)] h-[36px] px-[12px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full'"
                            tabindex="-1">
                            <Link v-if="!linkCopied" :size="16" stroke="currentColor" :stroke-width="2" />
                            <Check v-else :size="16" color="var(--text-primary)" />
                            {{ linkCopied ? t('Link Copied') : t('Copy link') }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>
              </span>

              <!-- View all files -->
              <button type="button" @click="handleFileListShow"
                class="p-[5px] flex items-center justify-center hover:bg-[var(--fill-tsp-white-dark)] rounded-lg cursor-pointer"
                :title="t('View all files in this task')">
                <FileSearch class="text-[var(--icon-secondary)]" :size="18" />
              </button>

              <!-- More options -->
              <button type="button" ref="moreBtnRef"
                class="p-[5px] flex items-center justify-center hover:bg-[var(--fill-tsp-white-dark)] rounded-lg cursor-pointer"
                :title="t('More options')"
                @click="handleMoreClick">
                <Ellipsis class="text-[var(--icon-secondary)]" :size="18" />
              </button>
            </div>
          </div>
          <div class="w-full flex justify-between items-center">
          </div>
        </div>
        <div class="flex-1"></div>
      </div>
      <div class="mx-auto w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] flex flex-col flex-1">
        <div class="flex flex-col w-full gap-[12px] pb-[80px] pt-[12px] flex-1 overflow-y-auto">
          <TakeControlBanner :visible="showTakeControlBanner" @takeControl="handleTakeControl" />
          <ChatMessage v-for="(message, index) in messages" :key="index" :message="message"
            :hideHeader="isConsecutiveAssistant(messages, index)"
            @toolClick="handleToolClick" />

          <!-- Loading indicator -->
          <LoadingIndicator v-if="isLoading" :text="$t('Thinking')" />
        </div>

        <div class="flex flex-col bg-[var(--background-gray-main)] sticky bottom-0">
          <button @click="handleFollow" v-if="!follow"
            class="flex items-center justify-center w-[36px] h-[36px] rounded-full bg-[var(--background-white-main)] hover:bg-[var(--background-gray-main)] clickable border border-[var(--border-main)] shadow-[0px_5px_16px_0px_var(--shadow-S),0px_0px_1.25px_0px_var(--shadow-S)] absolute -top-20 left-1/2 -translate-x-1/2">
            <ArrowDown class="text-[var(--icon-primary)]" :size="20" />
          </button>
          <PlanPanel v-if="plan && plan.steps.length > 0" :plan="plan" />
          <ChatBox v-model="inputMessage" v-model:attachments="attachments" :rows="1" @submit="handleSubmit"
            :isRunning="isLoading" @stop="handleStop" :placeholder="chatPlaceholder" />
        </div>
      </div>
    </div>
    <ToolPanel ref="toolPanel" :size="toolPanelSize" :sessionId="sessionId" :realTime="realTime"
      :isShare="false" :toolHistory="toolHistory"
      @jumpToRealTime="jumpToRealTime"
      @selectTool="handleSelectTool"
      @selectApp="handleSelectApp" />
  </SimpleBar>
</template>

<script setup lang="ts">
import SimpleBar from '../components/SimpleBar.vue';
import { ref, onMounted, watch, nextTick, onUnmounted, reactive, toRefs, computed } from 'vue';
import { useRouter, onBeforeRouteUpdate } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ChatBox from '../components/ChatBox.vue';
import ChatMessage from '../components/ChatMessage.vue';
import TakeControlBanner from '../components/TakeControlBanner.vue';
import * as agentApi from '../api/agent';
import { Message, MessageContent, ToolContent, AttachmentsContent, StepContent, isConsecutiveAssistant } from '../types/message';
import { PlanEventData, AgentSSEEvent } from '../types/event';
import { useAgentEvents } from '../composables/useAgentEvents';
import ToolPanel from '../components/ToolPanel.vue'
import type { ComputerApp } from '../components/ToolPanelContent.vue'
import PlanPanel from '../components/PlanPanel.vue';
import { ArrowDown, FileSearch, Lock, Globe, Link, Check, Ellipsis, ExternalLink, Copy, ChevronDown } from 'lucide-vue-next';
import ShareIcon from '@/components/icons/ShareIcon.vue';
import { showErrorToast, showSuccessToast } from '../utils/toast';
import type { FileInfo } from '../api/file';
import { useSessionFileList } from '../composables/useSessionFileList'
import { useFilePanel } from '../composables/useFilePanel'
import { copyToClipboard } from '../utils/dom'
import { SessionStatus } from '../types/response';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import LoadingIndicator from '@/components/ui/LoadingIndicator.vue';
import { useContextMenu, createMenuItem } from '../composables/useContextMenu';

const router = useRouter()
const { t } = useI18n()
const { showSessionFileList } = useSessionFileList()
const { hideFilePanel } = useFilePanel()

// Create initial state factory
const createInitialState = () => ({
  inputMessage: '',
  isLoading: false,
  sessionId: undefined as string | undefined,
  messages: [] as Message[],
  toolPanelSize: 0,
  realTime: true,
  follow: true,
  title: t('New Chat'),
  plan: undefined as PlanEventData | undefined,
  lastNoMessageTool: undefined as ToolContent | undefined,
  lastMessageTool: undefined as ToolContent | undefined,
  lastTool: undefined as ToolContent | undefined,
  lastEventId: undefined as string | undefined,
  cancelCurrentChat: null as (() => void) | null,
  attachments: [] as FileInfo[],
  shareMode: 'private' as 'private' | 'public', // Default to private mode
  linkCopied: false,
  sharingLoading: false // Loading state for share operations
});

// Create reactive state
const state = reactive(createInitialState());

// Destructure refs from reactive state
const {
  inputMessage,
  isLoading,
  sessionId,
  messages,
  toolPanelSize,
  realTime,
  follow,
  title,
  plan,
  lastNoMessageTool,
  lastTool,
  lastEventId,
  cancelCurrentChat,
  attachments,
  shareMode,
  linkCopied,
  sharingLoading
} = toRefs(state);

// Non-state refs that don't need reset
const toolPanel = ref<InstanceType<typeof ToolPanel>>()
const simpleBarRef = ref<InstanceType<typeof SimpleBar>>();
const observerRef = ref<HTMLDivElement>();
const chatContainerRef = ref<HTMLDivElement>();
const moreBtnRef = ref<HTMLElement | null>(null);
const modeMenuRef = ref<HTMLElement | null>(null);
const showModeMenu = ref(false);
const taskMode = ref<'agent' | 'chat'>((localStorage.getItem('manus-task-mode') as 'agent' | 'chat') || 'agent');
const sessionStatus = ref<SessionStatus | undefined>(undefined);
const { showContextMenu } = useContextMenu();

const toolHistory = computed(() => {
  const tools: ToolContent[] = [];
  for (const message of messages.value) {
    if (message.type === 'tool') {
      tools.push(message.content as ToolContent);
    } else if (message.type === 'step') {
      const step = message.content as StepContent;
      if (step.tools?.length) tools.push(...step.tools);
    }
  }
  return tools;
});

const showTakeControlBanner = computed(() => sessionStatus.value === SessionStatus.WAITING);

const chatPlaceholder = computed(() =>
  taskMode.value === 'chat' ? t('Send message to Manus') : t('Send message to Manus')
);

const setTaskMode = (mode: 'agent' | 'chat') => {
  taskMode.value = mode;
  localStorage.setItem('manus-task-mode', mode);
  showModeMenu.value = false;
};

// Shared SSE event -> message list conversion
const { handleEvent } = useAgentEvents(
  { messages, title, plan, isLoading, lastEventId, lastTool, lastNoMessageTool },
  {
    onToolActivity: (tool: ToolContent) => {
      if (realTime.value) {
        toolPanel.value?.showToolPanel(tool, true);
      }
    },
  }
);

// Reset all refs to their initial values
const resetState = () => {
  // Cancel any existing chat connection
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
  }

  // Reset reactive state to initial values
  Object.assign(state, createInitialState());
};

// Watch message changes and automatically scroll to bottom
watch(messages, async () => {
  await nextTick();
  if (follow.value) {
    simpleBarRef.value?.scrollToBottom();
  }
}, { deep: true });



const handleSubmit = () => {
  chat(inputMessage.value, attachments.value);
}

const chat = async (message: string = '', files: FileInfo[] = []) => {
  if (!sessionId.value) return;

  // Cancel any existing chat connection before starting a new one
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
    cancelCurrentChat.value = null;
  }

  if (message.trim()) {
    // Add user message to conversation list
    messages.value.push({
      type: 'user',
      content: {
        content: message,
        timestamp: Math.floor(Date.now() / 1000)
      } as MessageContent,
    });
  }

  if (files.length > 0) {
    messages.value.push({
      type: 'attachments',
      content: {
        role: 'user',
        attachments: files
      } as AttachmentsContent,
    });
  }

  // Automatically enable follow mode when sending message
  follow.value = true;

  // Clear input field and attachments
  inputMessage.value = '';
  attachments.value = [];
  isLoading.value = true;

  try {
    // Use the split event handler function and store the cancel function
    cancelCurrentChat.value = await agentApi.chatWithSession(
      sessionId.value,
      message,
      lastEventId.value,
      files.map((file: FileInfo) => ({file_id : file.file_id, 
                                        filename : file.filename})),
      {
        onOpen: () => {
          isLoading.value = true;
        },
        onMessage: ({ event, data }) => {
          handleEvent({
            event: event as AgentSSEEvent['event'],
            data: data as AgentSSEEvent['data']
          });
        },
        onClose: () => {
          isLoading.value = false;
          // Clear the cancel function when connection is closed normally
          if (cancelCurrentChat.value) {
            cancelCurrentChat.value = null;
          }
        },
        onError: (error) => {
          console.error('Chat error:', error);
          isLoading.value = false;
          // Clear the cancel function when there's an error
          if (cancelCurrentChat.value) {
            cancelCurrentChat.value = null;
          }
        }
      }
    );
  } catch (error) {
    console.error('Chat error:', error);
    isLoading.value = false;
    cancelCurrentChat.value = null;
  }
}

const restoreSession = async () => {
  if (!sessionId.value) {
    showErrorToast(t('Session not found'));
    return;
  }
  const session = await agentApi.getSession(sessionId.value);
  // Initialize share mode based on session state
  shareMode.value = session.is_shared ? 'public' : 'private';
  sessionStatus.value = session.status as SessionStatus;
  realTime.value = false;
  for (const event of session.events) {
    handleEvent(event);
  }
  realTime.value = true;
  if (session.status === SessionStatus.RUNNING || session.status === SessionStatus.PENDING) {
    await chat();
  }
  agentApi.clearUnreadMessageCount(sessionId.value);
}



onBeforeRouteUpdate((to, _, next) => {
  toolPanel.value?.hideToolPanel();
  hideFilePanel();
  resetState();
  if (to.params.sessionId) {
    messages.value = [];
    sessionId.value = String(to.params.sessionId) as string;
    restoreSession();
  }
  next();
})

// Initialize active conversation
onMounted(() => {
  hideFilePanel();
  document.addEventListener('mousedown', handleModeMenuOutside);
  const routeParams = router.currentRoute.value.params;
  if (routeParams.sessionId) {
    // If sessionId is included in URL, use it directly
    sessionId.value = String(routeParams.sessionId) as string;
    // Get initial message from history.state
    const message = history.state?.message;
    const files: FileInfo[] = history.state?.files;
    history.replaceState({}, document.title);
    if (message) {
      chat(message, files);
    } else {
      restoreSession();
    }
  }


});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleModeMenuOutside);
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
    cancelCurrentChat.value = null;
  }
})

const handleModeMenuOutside = (event: MouseEvent) => {
  if (showModeMenu.value && modeMenuRef.value && !modeMenuRef.value.contains(event.target as Node)) {
    showModeMenu.value = false;
  }
}

const isLastNoMessageTool = (tool: ToolContent) => {
  return tool.tool_call_id === lastNoMessageTool.value?.tool_call_id;
}

const isLiveTool = (tool: ToolContent) => {
  if (tool.status === 'calling') {
    return true;
  }
  if (!isLastNoMessageTool(tool)) {
    return false;
  }
  if (tool.timestamp > Date.now() - 5 * 60 * 1000) {
    return true;
  }
  return false;
}

const handleToolClick = (tool: ToolContent) => {
  realTime.value = false;
  if (sessionId.value) {
    toolPanel.value?.showToolPanel(tool, isLiveTool(tool));
  }
}

const jumpToRealTime = () => {
  realTime.value = true;
  if (lastNoMessageTool.value) {
    toolPanel.value?.showToolPanel(lastNoMessageTool.value, isLiveTool(lastNoMessageTool.value));
  }
}

const handleFollow = () => {
  follow.value = true;
  simpleBarRef.value?.scrollToBottom();
}

const handleScroll = (_: Event) => {
  follow.value = simpleBarRef.value?.isScrolledToBottom() ?? false;
}

const handleStop = () => {
  if (sessionId.value) {
    agentApi.stopSession(sessionId.value);
  }
}

const handleFileListShow = () => {
  showSessionFileList()
}

// Share functionality handlers
const handleShareModeChange = async (mode: 'private' | 'public') => {
  if (!sessionId.value || sharingLoading.value) return;
  
  // If mode is same as current, no need to call API
  if (shareMode.value === mode) {
    linkCopied.value = false;
    return;
  }
  
  try {
    sharingLoading.value = true;
    
    if (mode === 'public') {
      await agentApi.shareSession(sessionId.value);
    } else {
      await agentApi.unshareSession(sessionId.value);
    }
    
    shareMode.value = mode;
    linkCopied.value = false;
  } catch (error) {
    console.error('Error changing share mode:', error);
    showErrorToast(t('Failed to change sharing settings'));
  } finally {
    sharingLoading.value = false;
  }
}

const handleInstantShare = async () => {
  if (!sessionId.value) return;
  
  try {
    sharingLoading.value = true;
    await agentApi.shareSession(sessionId.value);
    shareMode.value = 'public';
    linkCopied.value = false;
  } catch (error) {
    console.error('Error sharing session:', error);
    showErrorToast(t('Failed to share session'));
  } finally {
    sharingLoading.value = false;
  }
}

const handleCopyLink = async () => {
  if (!sessionId.value) return;
  
  const shareUrl = `${window.location.origin}/share/${sessionId.value}`;
  
  try {
    const success = await copyToClipboard(shareUrl);
    
    if (success) {
      linkCopied.value = true;
      setTimeout(() => {
        linkCopied.value = false;
      }, 3000);
      showSuccessToast(t('Link copied to clipboard'));
    } else {
      showErrorToast(t('Failed to copy link'));
    }
  } catch (error) {
    console.error('Error copying share link:', error);
    showErrorToast(t('Failed to copy link'));
  }
}

const handleTakeControl = () => {
  if (!sessionId.value) return;
  // Prefer opening computer panel on latest browser tool, then enter takeover
  const browserTool = [...toolHistory.value].reverse().find((t) => t.name === 'browser');
  if (browserTool) {
    realTime.value = true;
    toolPanel.value?.showToolPanel(browserTool, true);
  }
  window.dispatchEvent(new CustomEvent('takeover', {
    detail: { sessionId: sessionId.value, active: true }
  }));
}

const handleSelectTool = (tool: ToolContent) => {
  realTime.value = false;
  toolPanel.value?.showToolPanel(tool, false);
}

const handleSelectApp = (app: ComputerApp) => {
  const match = [...toolHistory.value].reverse().find((tool) => {
    if (app === 'terminal') return tool.name === 'shell';
    if (app === 'file') return tool.name === 'file';
    if (app === 'search') return tool.name === 'info';
    return tool.name === 'browser';
  });
  if (match) {
    realTime.value = false;
    toolPanel.value?.showToolPanel(match, false);
  } else if (lastNoMessageTool.value) {
    toolPanel.value?.showToolPanel(lastNoMessageTool.value, isLiveTool(lastNoMessageTool.value));
  }
}

const getShareUrl = () => {
  if (!sessionId.value) return '';
  return `${window.location.origin}/share/${sessionId.value}`;
}

const shareToSocial = async (network: 'x' | 'linkedin' | 'facebook' | 'reddit') => {
  if (!sessionId.value) return;
  if (shareMode.value !== 'public') {
    try {
      sharingLoading.value = true;
      await agentApi.shareSession(sessionId.value);
      shareMode.value = 'public';
    } catch {
      showErrorToast(t('Failed to share session'));
      return;
    } finally {
      sharingLoading.value = false;
    }
  }
  const url = encodeURIComponent(getShareUrl());
  const text = encodeURIComponent(title.value || 'Manus');
  const targets: Record<string, string> = {
    x: `https://twitter.com/intent/tweet?url=${url}&text=${text}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
    reddit: `https://www.reddit.com/submit?url=${url}&title=${text}`,
  };
  window.open(targets[network], '_blank', 'noopener,noreferrer');
}

const handleMoreClick = (event: MouseEvent) => {
  const target = (moreBtnRef.value || event.currentTarget) as HTMLElement;
  if (!sessionId.value) return;
  const items = [
    createMenuItem('open', t('Open in new tab'), { icon: ExternalLink }),
    createMenuItem('copy', t('Copy link'), { icon: Copy }),
    createMenuItem('files', t('View all files in this task'), { icon: FileSearch }),
  ];
  showContextMenu(sessionId.value, target, items, async (key: string) => {
    if (key === 'open') {
      window.open(`/chat/${sessionId.value}`, '_blank');
    } else if (key === 'copy') {
      await handleCopyLink();
    } else if (key === 'files') {
      handleFileListShow();
    }
  });
}
</script>

