<template>
  <SimpleBar ref="simpleBarRef" @scroll="handleScroll">
    <!-- Chat column: full-bleed header (Manus) + centered message column -->
    <div ref="chatContainerRef" class="relative flex flex-col h-full flex-1 min-w-0">
      <!-- Official session chrome header bar (CDP: manus.im/app/…) -->
      <div ref="observerRef"
        class="flex h-[56px] w-full shrink-0 items-center justify-between py-[12px] md:px-[24px] ps-[16px] pe-[20px] md:ps-[16px] md:pe-[20px] gap-1 border-b sticky top-0 z-10 flex-shrink-0 [-webkit-app-region:drag] bg-[var(--background-gray-main)] border-[var(--border-main)]">
        <div class="flex min-w-0 flex-1 items-center gap-1">
          <div class="flex items-center pointer-events-auto relative" ref="modeMenuRef">
            <button
              type="button"
              class="flex h-8 pt-[7px] md:pr-[6px] pr-[4px] pb-[7px] md:pl-[8px] pl-[6px] justify-center items-center gap-1 rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-light)]"
              :aria-expanded="showModeMenu"
              aria-haspopup="menu"
              @click="toggleModeMenu">
              <span class="text-[var(--text-primary)] md:text-[18px] text-[16px] font-[500] md:leading-[22px] leading-[20px] truncate">Manus</span>
              <span
                v-if="taskMode === 'chat'"
                class="text-[var(--text-tertiary)] text-xs flex h-5 py-0.5 px-1.5 items-center rounded-[6px] border border-[var(--border-dark)] flex-shrink-0">
                Lite
              </span>
              <ChevronDown class="size-3.5 text-[var(--icon-tertiary)] shrink-0" :size="14" />
            </button>
          </div>
          <Teleport to="body">
            <div
              v-if="showModeMenu"
              ref="modeMenuPanelRef"
              role="menu"
              class="fixed z-[1100] min-w-[180px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] p-1"
              :style="{ top: `${modeMenuPos.top}px`, left: `${modeMenuPos.left}px` }">
              <button
                type="button"
                role="menuitem"
                class="flex w-full items-center justify-between gap-2 px-3 py-2 rounded-[8px] text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                @click="setTaskMode('agent')">
                <span>{{ t('Agent') }}</span>
                <Check v-if="taskMode === 'agent'" :size="16" class="text-[var(--icon-primary)]" />
              </button>
              <button
                type="button"
                role="menuitem"
                class="flex w-full items-center justify-between gap-2 px-3 py-2 rounded-[8px] text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                @click="setTaskMode('chat')">
                <span>{{ t('Chat') }} · Lite</span>
                <Check v-if="taskMode === 'chat'" :size="16" class="text-[var(--icon-primary)]" />
              </button>
            </div>
          </Teleport>
          <div class="flex-1 min-w-[16px]"></div>
        </div>

        <div class="flex flex-shrink-0 items-center gap-1 pointer-events-auto">
          <!-- Share — Manus SharePermission layout -->
          <Popover>
            <PopoverTrigger>
              <button type="button"
                class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors active:opacity-80 bg-transparent text-[var(--text-primary)] hover:opacity-100 hover:bg-[var(--fill-tsp-white-main)] h-[32px] min-w-[64px] px-[8px] rounded-[8px] gap-[4px] text-[14px] leading-[18px]"
                :class="shareMode === 'public' ? 'bg-[var(--fill-tsp-white-main)]' : ''">
                <ShareIcon color="var(--icon-secondary)" />
                <span class="text-[var(--text-secondary)]">{{ t('Share') }}</span>
              </button>
            </PopoverTrigger>
            <PopoverContent align="end">
              <div class="w-[400px] max-w-[calc(100vw-16px)] flex flex-col bg-[var(--background-menu-white)] rounded-2xl shadow-[0px_8px_32px_0px_var(--shadow-S),0px_0px_0px_1px_var(--border-light)]">
                <div class="flex py-3 px-4 justify-between items-center border-b border-[var(--border-main)]">
                  <h3 class="text-[var(--text-primary)] text-base font-medium leading-[22px]">{{ t('Share') }}</h3>
                  <span class="inline-flex ml-auto cursor-help" :title="t('Share privacy tip')">
                    <CircleHelp :size="16" class="text-[var(--icon-tertiary)]" />
                  </span>
                </div>
                <div class="pt-[12px] px-[16px] pb-[16px]">
                  <div @click="handleShareModeChange('private')"
                    :class="{'pointer-events-none opacity-50': sharingLoading}"
                    class="flex items-center gap-[10px] px-[8px] -mx-[8px] py-[8px] rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-main)]">
                    <div class="size-8 rounded-[8px] flex items-center justify-center bg-[var(--fill-tsp-white-dark)]">
                      <Lock :size="16" color="var(--icon-primary)" :stroke-width="2" />
                    </div>
                    <div class="flex flex-col flex-1 min-w-0">
                      <div class="text-[var(--text-primary)] text-sm font-medium">{{ t('Only me') }}</div>
                      <div class="text-[var(--text-tertiary)] text-[13px]">{{ t('Viewable by yourself only') }}</div>
                    </div>
                    <Check :size="20" :class="shareMode === 'private' ? 'ml-auto' : 'ml-auto invisible'" color="var(--icon-primary)" />
                  </div>
                  <div @click="handleShareModeChange('public')"
                    :class="{'pointer-events-none opacity-50': sharingLoading}"
                    class="flex items-center gap-[10px] px-[8px] -mx-[8px] py-[8px] rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-main)]">
                    <div class="size-8 rounded-[8px] flex items-center justify-center bg-[var(--fill-tsp-white-dark)]">
                      <Globe :size="16" color="var(--icon-primary)" :stroke-width="2" />
                    </div>
                    <div class="flex flex-col flex-1 min-w-0">
                      <div class="text-[var(--text-primary)] text-sm font-medium">{{ t('Public access') }}</div>
                      <div class="text-[var(--text-tertiary)] text-[13px]">{{ t('Anyone with a link can view') }}</div>
                    </div>
                    <Check :size="20" :class="shareMode === 'public' ? 'ml-auto' : 'ml-auto invisible'" color="var(--icon-primary)" />
                  </div>

                  <div v-if="shareMode === 'private'" class="mt-2">
                    <button @click.stop="handleInstantShare" :disabled="sharingLoading"
                      class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 bg-[var(--Button-primary-black)] text-[var(--text-onblack)] h-[36px] px-[12px] rounded-[10px] gap-[6px] text-sm w-full disabled:opacity-50">
                      <div v-if="sharingLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <Link v-else :size="16" stroke="currentColor" :stroke-width="2" />
                      {{ sharingLoading ? t('Sharing...') : t('Share Instantly') }}
                    </button>
                  </div>
                  <!-- Manus: SocialMediaShare left + Copy link right -->
                  <div v-else class="mt-2 space-y-2">
                    <div class="flex items-center justify-between gap-2">
                      <div class="flex items-center gap-2">
                        <button type="button" class="size-9 rounded-full bg-[var(--fill-tsp-white-dark)] flex items-center justify-center hover:opacity-80" title="X" @click="shareToSocial('x')">
                          <span class="text-sm font-bold text-[var(--text-primary)]">𝕏</span>
                        </button>
                        <button type="button" class="size-9 rounded-full bg-[var(--fill-tsp-white-dark)] flex items-center justify-center hover:opacity-80 text-[12px] font-semibold text-[var(--text-primary)]" @click="shareToSocial('linkedin')">in</button>
                        <button type="button" class="size-9 rounded-full bg-[var(--fill-tsp-white-dark)] flex items-center justify-center hover:opacity-80 text-[13px] font-semibold text-[var(--text-primary)]" @click="shareToSocial('facebook')">f</button>
                        <button type="button" class="size-9 rounded-full bg-[var(--fill-tsp-white-dark)] flex items-center justify-center hover:opacity-80 text-[11px] font-semibold text-[var(--text-primary)]" @click="shareToSocial('reddit')">r/</button>
                      </div>
                      <button @click.stop="handleCopyLink"
                        class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-[36px] px-[12px] rounded-[10px] gap-[6px] text-sm shrink-0"
                        :class="linkCopied
                          ? 'bg-[var(--Button-primary-white)] text-[var(--text-primary)] border border-[var(--border-btn-main)]'
                          : 'bg-[var(--Button-primary-black)] text-[var(--text-onblack)] hover:opacity-90'">
                        <Link v-if="!linkCopied" :size="16" stroke="currentColor" :stroke-width="2" />
                        <Check v-else :size="16" color="var(--text-primary)" />
                        {{ linkCopied ? t('Link copied') : t('Copy link') }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </PopoverContent>
          </Popover>

          <button type="button" @click="handleFileListShow"
            class="flex items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-white-light)] size-8"
            :title="t('View all files in this task')">
            <FileSearch class="size-[18px] text-[var(--icon-secondary)]" :size="18" />
          </button>

          <!-- Official session More (div.size-8 + Ellipsis) -->
          <div
            ref="moreBtnRef"
            role="button"
            tabindex="0"
            class="flex items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-white-light)] size-8"
            :title="t('More options')"
            @click="handleMoreClick"
            @keydown.enter.prevent="handleMoreClick($event)">
            <Ellipsis class="size-[18px] text-[var(--icon-secondary)]" :size="18" />
          </div>
        </div>
      </div>

      <!-- Official message column (CDP session detail): px-[24px] sm:max-w-[810px] sm:min-w-[360px] -->
      <div class="mx-auto w-full max-w-full px-[24px] sm:max-w-[810px] sm:min-w-[360px] flex flex-col flex-1">
        <div class="flex flex-col w-full gap-[12px] pb-[80px] pt-[12px] flex-1 overflow-y-auto">
          <ChatMessage v-for="(message, index) in messages" :key="index" :message="message"
            :hideHeader="isConsecutiveAssistant(messages, index)"
            :showLiteBadge="taskMode === 'chat'"
            :showCopyActions="shouldShowAssistantCopyActions(index)"
            :isLastBeforeUser="isAssistantLastBeforeUser(index)"
            @toolClick="handleToolClick" />
          <ChatWaitingContinue
            :visible="showWaitingContinue"
            :copy-text="lastAssistantPlainText" />
          <ChatTaskCompleted
            :visible="showTaskCompleted"
            :copy-text="lastAssistantPlainText" />
          <!-- AgentIsTyping: only fill the empty gap before first visible turn output -->
          <LoadingIndicator v-if="showThinking" :text="$t('{name} is thinking', { name: 'Manus' })" />
          <!-- Official running spacer when work is already visible (tools/steps/messages) -->
          <div v-else-if="isBusy" aria-hidden="true" class="h-5 invisible" />
        </div>

        <div class="flex flex-col bg-[var(--background-gray-main)] sticky bottom-0">
          <button @click="handleFollow" v-if="!follow"
            class="flex items-center justify-center w-[36px] h-[36px] rounded-full bg-[var(--background-white-main)] hover:bg-[var(--background-gray-main)] clickable border border-[var(--border-main)] shadow-[0px_5px_16px_0px_var(--shadow-S),0px_0px_1.25px_0px_var(--shadow-S)] absolute -top-20 left-1/2 -translate-x-1/2">
            <ArrowDown class="text-[var(--icon-primary)]" :size="20" />
          </button>
          <TakeControlBanner
            :visible="showTakeControlBanner"
            @takeControl="handleTakeControl" />
          <ChatBox v-model="inputMessage" v-model:attachments="attachments" :rows="1" dense @submit="handleSubmit"
            :isRunning="isBusy" @stop="handleStop" :placeholder="chatPlaceholder" />
        </div>
      </div>
    </div>
    <ComputerPanel ref="computerPanel" :sessionId="sessionId" :realTime="realTime"
      :isShare="false" :toolHistory="toolHistory" :plan="plan"
      @jumpToRealTime="jumpToRealTime"
      @selectTool="handleSelectTool"
      @useComputer="handleTakeControl" />
  </SimpleBar>
</template>

<script setup lang="ts">
import SimpleBar from '../components/SimpleBar.vue';
import { ref, onMounted, watch, nextTick, onUnmounted, reactive, toRefs, computed } from 'vue';
import { useRouter, onBeforeRouteUpdate } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ChatBox from '../components/ChatBox.vue';
import ChatMessage from '../components/ChatMessage.vue';
import ChatTaskCompleted from '../components/ChatTaskCompleted.vue';
import ChatWaitingContinue from '../components/ChatWaitingContinue.vue';
import TakeControlBanner from '../components/TakeControlBanner.vue';
import * as agentApi from '../api/agent';
import { Message, MessageContent, ToolContent, StepContent, isConsecutiveAssistant } from '../types/message';
import { PlanEventData, AgentEvent, type TerminalUpdateEventData, type FileUpdateEventData } from '../types/event';
import { useAgentEvents } from '../composables/useAgentEvents';
import { useSessionPhase } from '../composables/useSessionPhase';
import ComputerPanel from '../components/ComputerPanel.vue'
import { ArrowDown, FileSearch, Lock, Globe, Link, Check, Ellipsis, Pencil, Star, Trash, FolderPlus, Folder, FolderSync, Pin, ChevronDown } from 'lucide-vue-next';
import ShareIcon from '@/components/icons/ShareIcon.vue';
import { showErrorToast, showSuccessToast } from '../utils/toast';
import type { FileInfo } from '../api/file';
import { useSessionFileList } from '../composables/useSessionFileList'
import { useFilePreviewer } from '../composables/useFilePreviewer'
import { copyToClipboard } from '../utils/dom'
import { SessionStatus, type ProjectItem } from '../types/response';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import LoadingIndicator from '@/components/ui/LoadingIndicator.vue';
import { useContextMenu, createMenuItem, createDangerMenuItem, createSeparator, createSubmenuItem } from '../composables/useContextMenu';
import { useDialog } from '../composables/useDialog';
import { getProjects, createProject } from '../api/project';
import { eventBus } from '../utils/eventBus';

const router = useRouter()
const { t } = useI18n()
const { showSessionFileList } = useSessionFileList()
const { hideFilePreviewer } = useFilePreviewer()
const { showConfirmDialog, showInputDialog } = useDialog();
const projects = ref<ProjectItem[]>([]);
const isFavorite = ref(false);
const isPinned = ref(false);
const projectId = ref<string | null>(null);
const taskMode = ref<'agent' | 'chat'>('agent');

// Create initial state factory
const createInitialState = () => ({
  inputMessage: '',
  sessionId: undefined as string | undefined,
  messages: [] as Message[],
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
  sessionId,
  messages,
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

const {
  phase,
  isBusy,
  hydrateFromSessionStatus,
  applyStatusUpdate,
  noteOptimisticRun,
  noteDomainEvent,
  reset: resetPhase,
  showWaitingContinue,
  showTaskCompleted,
  showThinking,
} = useSessionPhase({ messages });

// Non-state refs that don't need reset
const isHydrating = ref(false)
const computerPanel = ref<InstanceType<typeof ComputerPanel>>()
const simpleBarRef = ref<InstanceType<typeof SimpleBar>>();
const observerRef = ref<HTMLDivElement>();
const chatContainerRef = ref<HTMLDivElement>();
const moreBtnRef = ref<HTMLElement | null>(null);
const modeMenuRef = ref<HTMLElement | null>(null);
const modeMenuPanelRef = ref<HTMLElement | null>(null);
const modeMenuPos = ref({ top: 0, left: 0 });
const showModeMenu = ref(false);
const { showContextMenu } = useContextMenu();

const toggleModeMenu = () => {
  if (!showModeMenu.value && modeMenuRef.value) {
    const r = modeMenuRef.value.getBoundingClientRect();
    modeMenuPos.value = { top: r.bottom + 6, left: r.left };
  }
  showModeMenu.value = !showModeMenu.value;
};

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

const hasBrowserTool = computed(() =>
  toolHistory.value.some((t) => t.name === 'browser'),
);

/** Official suggest-takeover banner: waiting + browser tool available */
const showTakeControlBanner = computed(() =>
  phase.value === 'waiting' && !isBusy.value && hasBrowserTool.value,
);

const chatPlaceholder = computed(() => t('Send message to Manus'));

const setTaskMode = async (mode: 'agent' | 'chat') => {
  showModeMenu.value = false;
  if (!sessionId.value || taskMode.value === mode) return;
  const prev = taskMode.value;
  taskMode.value = mode;
  try {
    await agentApi.updateSessionTaskMode(sessionId.value, mode);
  } catch (e) {
    taskMode.value = prev;
    console.error('Failed to update task mode', e);
    showErrorToast(t('Failed to update mode'));
  }
};

const handleModeMenuOutside = (e: MouseEvent) => {
  if (!showModeMenu.value) return;
  const t = e.target as Node;
  if (modeMenuRef.value?.contains(t) || modeMenuPanelRef.value?.contains(t)) return;
  showModeMenu.value = false;
};

const handleModeMenuScroll = () => {
  if (showModeMenu.value) showModeMenu.value = false;
};

const lastAssistantIndex = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].type === 'assistant') return i;
  }
  return -1;
});

const lastAssistantPlainText = computed(() => {
  const i = lastAssistantIndex.value;
  if (i < 0) return '';
  return ((messages.value[i].content as MessageContent).content || '').trim();
});

/**
 * Official ChatReplyActions: show Copy under assistant replies that are not the
 * live last message (TaskCompleted footer owns copy when task is done).
 */
const shouldShowAssistantCopyActions = (index: number) => {
  const m = messages.value[index];
  if (m?.type !== 'assistant') return false;
  if (!((m.content as MessageContent).content || '').trim()) return false;
  if (isBusy.value || phase.value === 'running' || phase.value === 'pending') {
    return index !== lastAssistantIndex.value;
  }
  if (showTaskCompleted.value || showWaitingContinue.value) {
    return index !== lastAssistantIndex.value;
  }
  return true;
};

const isAssistantLastBeforeUser = (index: number) => {
  if (messages.value[index]?.type !== 'assistant') return false;
  for (let i = index + 1; i < messages.value.length; i++) {
    const t = messages.value[i].type;
    if (t === 'user') return true;
    if (t === 'assistant') return false;
  }
  return false;
};

// Shared agent event -> message list conversion
const { handleEvent: handleAgentEvent } = useAgentEvents(
  { messages, title, plan, lastEventId, lastTool, lastNoMessageTool },
  {
    onToolActivity: (tool: ToolContent) => {
      if (realTime.value) {
        computerPanel.value?.showComputerPanel(tool, true);
      }
    },
    onStreamError: () => {
      if (!isHydrating.value) noteDomainEvent('error');
    },
  }
);

const handleEvent = (event: AgentEvent) => {
  handleAgentEvent(event);
  if (isHydrating.value) return;
  if (event.event === 'status_update') return;
  if (event.event === 'wait') noteDomainEvent('wait');
  else if (event.event === 'done') noteDomainEvent('done');
};

// Reset all refs to their initial values
const resetState = () => {
  const prevSessionId = sessionId.value;
  // Drop local stream handlers; leave WS subscription for previous session
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
    cancelCurrentChat.value = null;
  }
  if (prevSessionId) {
    void agentApi.leaveChatSession(prevSessionId);
  }

  // Reset reactive state to initial values
  Object.assign(state, createInitialState());
  resetPhase();
  isFavorite.value = false;
  isPinned.value = false;
  projectId.value = null;
  taskMode.value = 'agent';
  projects.value = [];
};

// Watch message changes and automatically scroll to bottom
watch(messages, async () => {
  await nextTick();
  if (follow.value) {
    simpleBarRef.value?.scrollToBottom();
  }
}, { deep: true });



const chatStreamCallbacks = (): agentApi.ChatStreamCallbacks => ({
  onOpen: () => {
    // Keep loading only when we already marked a turn in flight (chat send)
  },
  onMessage: ({ event, data }) => {
    if (event === 'terminal_update') {
      const d = data as TerminalUpdateEventData;
      if (!sessionId.value) return;
      eventBus.emit('tool:terminal_update', {
        sessionId: sessionId.value,
        shellId: d.shell_id,
        output: d.output,
      });
      return;
    }
    if (event === 'file_update') {
      const d = data as FileUpdateEventData;
      if (!sessionId.value) return;
      eventBus.emit('tool:file_update', {
        sessionId: sessionId.value,
        path: d.path,
        content: d.content,
        oldContent: d.old_content,
        file: d.file ?? null,
      });
      return;
    }
    handleEvent({
      event: event as AgentEvent['event'],
      data: data as AgentEvent['data'],
    });
  },
  onStatusUpdate: (agentStatus) => {
    applyStatusUpdate(agentStatus);
  },
  onClose: () => {
    // Loading is driven by status_update (follows stream_end). Do not clear here.
    if (cancelCurrentChat.value) {
      cancelCurrentChat.value = null;
    }
  },
  onError: (error) => {
    console.error('Chat error:', error);
    noteDomainEvent('error');
    if (cancelCurrentChat.value) {
      cancelCurrentChat.value = null;
    }
  },
});

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

  if (message.trim() || files.length > 0) {
    // Official ChatQuestion: attachments + text in one right-aligned group
    messages.value.push({
      type: 'user',
      content: {
        content: message,
        timestamp: Math.floor(Date.now() / 1000),
        attachments: files.length > 0 ? files : undefined,
      } as MessageContent,
    });
  }

  // Automatically enable follow mode when sending message
  follow.value = true;

  // Clear input field and attachments
  inputMessage.value = '';
  attachments.value = [];
  noteOptimisticRun();

  try {
    cancelCurrentChat.value = await agentApi.chatWithSession(
      sessionId.value,
      message,
      lastEventId.value,
      files.map((file: FileInfo) => ({file_id : file.file_id, 
                                        filename : file.filename})),
      {
        ...chatStreamCallbacks(),
        onOpen: () => {
          noteOptimisticRun();
        },
      }
    );
  } catch (error) {
    console.error('Chat error:', error);
    noteDomainEvent('error');
    cancelCurrentChat.value = null;
  }
}

const restoreSession = async () => {
  if (!sessionId.value) {
    showErrorToast(t('Session not found'));
    return;
  }
  const session = await agentApi.getSession(sessionId.value);
  applySessionMeta(session);
  realTime.value = false;
  isHydrating.value = true;
  try {
    hydrateFromSessionStatus(session.status);
    for (const event of session.events) {
      handleAgentEvent(event);
    }
  } finally {
    isHydrating.value = false;
  }
  realTime.value = true;

  // Always join the chat channel (status_update + idle Mongo catch-up).
  // Only resume the live Redis stream while the agent is running.
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
    cancelCurrentChat.value = null;
  }
  try {
    if (session.status === SessionStatus.RUNNING) {
      noteOptimisticRun();
      cancelCurrentChat.value = await agentApi.chatWithSession(
        sessionId.value,
        '',
        lastEventId.value,
        undefined,
        {
          ...chatStreamCallbacks(),
          onOpen: () => {
            noteOptimisticRun();
          },
        },
      );
    } else {
      cancelCurrentChat.value = await agentApi.chatWithSession(
        sessionId.value,
        '',
        lastEventId.value,
        undefined,
        chatStreamCallbacks(),
      );
    }
  } catch (error) {
    console.error('Failed to join chat session:', error);
    noteDomainEvent('error');
    cancelCurrentChat.value = null;
  }
  agentApi.clearUnreadMessageCount(sessionId.value);
}



onBeforeRouteUpdate((to, _, next) => {
  computerPanel.value?.hideComputerPanel();
  hideFilePreviewer();
  resetState();
  if (to.params.sessionId) {
    messages.value = [];
    sessionId.value = String(to.params.sessionId) as string;
    restoreSession();
  }
  next();
})

const applySessionMeta = (session: Awaited<ReturnType<typeof agentApi.getSession>>) => {
  shareMode.value = session.is_shared ? 'public' : 'private';
  isFavorite.value = !!session.is_favorite;
  isPinned.value = !!session.is_pinned;
  projectId.value = session.project_id ?? null;
  taskMode.value = session.task_mode === 'chat' ? 'chat' : 'agent';
};

// Initialize active conversation
onMounted(() => {
  document.addEventListener('mousedown', handleModeMenuOutside);
  window.addEventListener('scroll', handleModeMenuScroll, true);
  hideFilePreviewer();
  const routeParams = router.currentRoute.value.params;
  if (routeParams.sessionId) {
    // If sessionId is included in URL, use it directly
    sessionId.value = String(routeParams.sessionId) as string;
    // Get initial message / mode from history.state (HomePage → new chat)
    const message = history.state?.message as string | undefined;
    const files = history.state?.files as FileInfo[] | undefined;
    const seededMode = history.state?.taskMode as 'agent' | 'chat' | undefined;
    history.replaceState({}, document.title);
    if (seededMode === 'chat' || seededMode === 'agent') {
      taskMode.value = seededMode;
    }
    if (message || (files && files.length > 0)) {
      // Initial-message path used to skip restoreSession(), so taskMode never
      // left the default 'agent'. Load session meta first, then send.
      void (async () => {
        try {
          const session = await agentApi.getSession(sessionId.value!);
          applySessionMeta(session);
        } catch (e) {
          console.error('Failed to load session meta before initial chat', e);
        }
        await chat(message || '', files || []);
      })();
    } else {
      restoreSession();
    }
  }
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleModeMenuOutside);
  window.removeEventListener('scroll', handleModeMenuScroll, true);
  const prevSessionId = sessionId.value;
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
    cancelCurrentChat.value = null;
  }
  if (prevSessionId) {
    void agentApi.leaveChatSession(prevSessionId);
  }
})

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
  // tool.timestamp is Unix seconds (see backend event serializers)
  if (tool.timestamp > Math.floor(Date.now() / 1000) - 5 * 60) {
    return true;
  }
  return false;
}

const handleToolClick = (tool: ToolContent) => {
  realTime.value = false;
  if (sessionId.value) {
    computerPanel.value?.showComputerPanel(tool, isLiveTool(tool));
  }
}

const jumpToRealTime = () => {
  realTime.value = true;
  if (lastNoMessageTool.value) {
    computerPanel.value?.showComputerPanel(lastNoMessageTool.value, isLiveTool(lastNoMessageTool.value));
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
    computerPanel.value?.showComputerPanel(browserTool, true);
  }
  eventBus.emit('ui:takeover', {
    sessionId: sessionId.value,
    active: true,
  });
}

const handleSelectTool = (tool: ToolContent) => {
  realTime.value = false;
  computerPanel.value?.showComputerPanel(tool, false);
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

const handleMoreClick = async (event: MouseEvent | KeyboardEvent) => {
  event.stopPropagation();
  const target = (moreBtnRef.value || event.currentTarget) as HTMLElement;
  if (!sessionId.value) return;

  // Official session-detail … menu: Rename / Move to project / — / Pin / Favorite / Delete
  // (skip scheduled / archive — no local product support)
  try {
    const res = await getProjects();
    projects.value = res.projects ?? [];
  } catch {
    projects.value = [];
  }

  const favoritedNow = isFavorite.value;
  const pinnedNow = isPinned.value;
  const items = [
    createMenuItem('rename', t('Rename'), { icon: Pencil }),
  ];

  // Official:「移动到项目」+ chevron → submenu (新项目 / — / projects)
  const moveChildren = [
    createMenuItem('new_project', t('New project'), { icon: FolderPlus }),
    createSeparator(),
    ...projects.value.map((project) =>
      createMenuItem(`move:${project.project_id}`, project.name, {
        icon: Folder,
        checked: project.project_id === projectId.value,
      }),
    ),
  ];
  if (projectId.value) {
    moveChildren.push(createSeparator());
    moveChildren.push(createMenuItem('remove_project', t('Remove from project'), { icon: Folder }));
  }
  items.push(createSubmenuItem('move_project', t('Move to project'), moveChildren, { icon: FolderSync }));

  items.push(createSeparator());
  items.push(createMenuItem('pin', pinnedNow ? t('Unpin') : t('Pin'), { icon: Pin }));
  items.push(createMenuItem('favorite', favoritedNow ? t('Unfavorite') : t('Add to favorites'), { icon: Star }));
  items.push(createDangerMenuItem('delete', t('Delete'), { icon: Trash }));

  showContextMenu(sessionId.value, target, items, async (key: string) => {
    if (key === 'rename') {
      showInputDialog({
        title: t('Rename'),
        initialValue: title.value || '',
        placeholder: t('Enter task name'),
        confirmText: t('Save'),
        onConfirm: async (value: string) => {
          if (!value || !sessionId.value) return;
          try {
            const result = await agentApi.updateSessionTitle(sessionId.value, value);
            title.value = result.title;
            showSuccessToast(t('Renamed successfully'));
          } catch {
            showErrorToast(t('Failed to rename session'));
          }
        },
      });
    } else if (key === 'pin') {
      if (!sessionId.value) return;
      try {
        const result = await agentApi.pinSession(sessionId.value, !pinnedNow);
        isPinned.value = result.is_pinned;
        showSuccessToast(result.is_pinned ? t('Task pinned') : t('Task unpinned'));
      } catch {
        showErrorToast(t('Failed to update pin'));
      }
    } else if (key === 'favorite') {
      if (!sessionId.value) return;
      try {
        const result = favoritedNow
          ? await agentApi.unfavoriteSession(sessionId.value)
          : await agentApi.favoriteSession(sessionId.value);
        isFavorite.value = result.is_favorite;
        showSuccessToast(result.is_favorite ? t('Added to favorite') : t('Removed from favorite'));
      } catch {
        showErrorToast(t('Failed to update favorite'));
      }
    } else if (key === 'new_project') {
      if (!sessionId.value) return;
      showInputDialog({
        title: t('New project'),
        placeholder: t('Enter project name'),
        confirmText: t('Create'),
        onConfirm: async (value: string) => {
          if (!value || !sessionId.value) return;
          try {
            const project = await createProject(value);
            await agentApi.moveSessionProject(sessionId.value, project.project_id);
            projectId.value = project.project_id;
            projects.value = [project, ...projects.value];
            eventBus.emit('projects:changed');
            showSuccessToast(t('Moved to project'));
          } catch {
            showErrorToast(t('Failed to create project'));
          }
        },
      });
    } else if (key.startsWith('move:')) {
      if (!sessionId.value) return;
      const nextProjectId = key.slice(5);
      if (nextProjectId === projectId.value) return;
      try {
        await agentApi.moveSessionProject(sessionId.value, nextProjectId);
        projectId.value = nextProjectId;
        showSuccessToast(t('Moved to project'));
      } catch {
        showErrorToast(t('Failed to move session'));
      }
    } else if (key === 'remove_project') {
      if (!sessionId.value) return;
      try {
        await agentApi.moveSessionProject(sessionId.value, null);
        projectId.value = null;
        showSuccessToast(t('Removed from project'));
      } catch {
        showErrorToast(t('Failed to move session'));
      }
    } else if (key === 'delete') {
      showConfirmDialog({
        title: t('Delete this task?'),
        content: t('The chat history of this session cannot be recovered after deletion.'),
        confirmText: t('Delete'),
        cancelText: t('Cancel'),
        confirmType: 'danger',
        onConfirm: () => {
          if (!sessionId.value) return;
          agentApi.deleteSession(sessionId.value).then(() => {
            showSuccessToast(t('Deleted successfully'));
            router.push('/');
          }).catch(() => {
            showErrorToast(t('Failed to delete session'));
          });
        },
      });
    }
  });
}
</script>

