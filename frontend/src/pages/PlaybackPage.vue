<template>
  <SimpleBar ref="simpleBarRef" @scroll="handleScroll">
    <div ref="chatContainerRef"
      class="relative flex flex-col h-full flex-1 min-w-0 mx-auto w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] px-5">
      
      <!-- 回放控制栏 -->
      <div class="playback-controls sticky top-0 z-20 bg-[var(--background-gray-main)] p-3 mb-2 rounded-lg shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-[var(--text-primary)]">🎬 Playback Mode</span>
            <span class="text-xs text-[var(--text-secondary)]">{{ events.length }} events</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-1">
              <button @click="reset" class="btn-playback" title="Reset">
                <RotateCcw :size="16" />
              </button>
              <button @click="stepBackward" class="btn-playback" :disabled="currentEventIndex <= 0" title="Previous">
                <SkipBack :size="16" />
              </button>
              <button @click="togglePlayback" class="btn-playback btn-play" :title="isPlaying ? 'Pause' : 'Play'">
                <Play v-if="!isPlaying" :size="16" />
                <Pause v-else :size="16" />
              </button>
              <button @click="stepForward" class="btn-playback" :disabled="currentEventIndex >= events.length - 1" title="Next">
                <SkipForward :size="16" />
              </button>
            </div>
            <div class="flex items-center gap-2">
              <input 
                type="range" 
                v-model="currentEventIndex" 
                :min="0" 
                :max="Math.max(0, events.length - 1)" 
                class="progress-slider" 
                @input="handleSliderChange" 
              />
              <span class="text-xs text-[var(--text-secondary)] min-w-[60px]">
                {{ currentEventIndex + 1 }} / {{ events.length }}
              </span>
            </div>
            <select v-model="playbackSpeed" class="speed-select">
              <option value="0.5">0.5x</option>
              <option value="1">1x</option>
              <option value="2">2x</option>
              <option value="4">4x</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 标题栏 -->
      <div ref="observerRef"
        class="sticky top-0 z-10 bg-[var(--background-gray-main)] flex-shrink-0 flex flex-row items-center justify-between pt-4 pb-1">
        <div class="flex w-full flex-col gap-[4px]">
          <div
            :class="['text-[var(--text-primary)] text-lg font-medium w-full flex flex-row items-center justify-between flex-1 min-w-0 gap-2', { 'ps-7': shouldAddPaddingClass }]">
            <div class="flex flex-row items-center gap-[6px] flex-1 min-w-0">
              <span class="whitespace-nowrap text-ellipsis overflow-hidden">
                {{ title }}
              </span>
              <span class="text-xs text-[var(--text-tertiary)] bg-[var(--background-white-main)] px-2 py-1 rounded">
                Shared {{ formatSharedDate(sharedAt) }}
              </span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <button @click="handleFileListShow"
                class="p-[5px] flex items-center justify-center hover:bg-[var(--fill-tsp-white-dark)] rounded-lg cursor-pointer">
                <FileSearch class="text-[var(--icon-secondary)]" :size="18" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="flex flex-col w-full gap-[12px] pb-[80px] pt-[12px] flex-1 overflow-y-auto">
        <div v-if="loading" class="flex items-center justify-center py-8">
          <div class="text-[var(--text-secondary)]">Loading shared conversation...</div>
        </div>
        <div v-else-if="error" class="flex items-center justify-center py-8">
          <div class="text-red-500">{{ error }}</div>
        </div>
        <div v-else-if="events.length === 0" class="flex items-center justify-center py-8">
          <div class="text-[var(--text-secondary)]">This conversation has no messages yet.</div>
        </div>
        <template v-else>
          <ChatMessage v-for="(message, index) in displayedMessages" :key="index" :message="message"
            @toolClick="handleToolClick" />
        </template>

        <!-- 加载指示器（回放时显示） -->
        <div v-if="isPlaying && currentEventIndex < events.length - 1" 
             class="flex items-center gap-1 text-[var(--text-tertiary)] text-sm">
          <span>Playing back...</span>
          <span class="flex gap-1 relative top-[4px]">
            <span class="w-[3px] h-[3px] rounded animate-bounce-dot bg-[var(--icon-tertiary)]" style="animation-delay: 0ms;"></span>
            <span class="w-[3px] h-[3px] rounded animate-bounce-dot bg-[var(--icon-tertiary)]" style="animation-delay: 200ms;"></span>
            <span class="w-[3px] h-[3px] rounded animate-bounce-dot bg-[var(--icon-tertiary)]" style="animation-delay: 400ms;"></span>
          </span>
        </div>
      </div>

      <!-- 底部输入框（只读模式） -->
      <div class="flex flex-col bg-[var(--background-gray-main)] sticky bottom-0">
        <template v-if="plan && plan.steps.length > 0">
          <PlanPanel :plan="plan" />
        </template>
        <div class="p-4 text-center text-[var(--text-secondary)] bg-[var(--background-white-main)] rounded-lg mx-4 mb-4">
          <div class="flex items-center justify-center gap-2">
            <Eye :size="16" />
            <span>Read-only mode - This is a shared conversation</span>
          </div>
        </div>
      </div>
    </div>
    <RightPanel ref="rightPanel" :size="toolPanelSize" :sessionId="sessionId" :realTime="false"
      @jumpToRealTime="jumpToRealTime" />
  </SimpleBar>
</template>

<script setup lang="ts">
import SimpleBar from '../components/SimpleBar.vue';
import { ref, onMounted, watch, nextTick, onUnmounted, reactive, toRefs } from 'vue';
import { useRoute } from 'vue-router';
import ChatMessage from '../components/ChatMessage.vue';
import { Message, MessageContent, ToolContent, StepContent, AttachmentsContent } from '../types/message';
import {
  StepEventData,
  ToolEventData,
  MessageEventData,
  ErrorEventData,
  TitleEventData,
  PlanEventData,
  AgentSSEEvent,
} from '../types/event';
import RightPanel from '../components/RightPanel.vue';
import PlanPanel from '../components/PlanPanel.vue';
import { FileSearch, Play, Pause, SkipBack, SkipForward, RotateCcw, Eye } from 'lucide-vue-next';
import { getSharedSession } from '../api/agent';
import { eventBus } from '../utils/eventBus';
import { EVENT_SESSION_FILE_LIST_SHOW } from '../constants/event';
import type { FileInfo } from '../api/file';

const route = useRoute();

// 创建初始状态
const createInitialState = () => ({
  sessionId: '',
  messages: [] as Message[],
  toolPanelSize: 0,
  realTime: false,
  follow: true,
  title: 'Shared Conversation',
  plan: undefined as PlanEventData | undefined,
  lastNoMessageTool: undefined as ToolContent | undefined,
  lastMessageTool: undefined as ToolContent | undefined,
  lastTool: undefined as ToolContent | undefined,
  shouldAddPaddingClass: false,
});

// 创建响应式状态
const state = reactive(createInitialState());

// 解构 refs
const {
  sessionId,
  messages,
  toolPanelSize,
  realTime,
  follow,
  title,
  plan,
  lastNoMessageTool,
  lastMessageTool,
  lastTool,
  shouldAddPaddingClass,
} = toRefs(state);

// 回放相关状态
const events = ref<AgentSSEEvent[]>([]);
const currentEventIndex = ref<number>(0);
const isPlaying = ref<boolean>(false);
const playbackSpeed = ref<number>(2);
const sharedAt = ref<number>(0);
const loading = ref<boolean>(true);
const error = ref<string>('');
const displayedMessages = ref<Message[]>([]);
const sharedFiles = ref<FileInfo[]>([]);

// 非状态 refs
const rightPanel = ref();
const simpleBarRef = ref<InstanceType<typeof SimpleBar>>();
const observerRef = ref<HTMLDivElement>();
const chatContainerRef = ref<HTMLDivElement>();

let playbackInterval: number | null = null;

// 位置监控函数
const checkElementPosition = () => {
  const element = observerRef.value;
  if (element) {
    const rect = element.getBoundingClientRect();
    shouldAddPaddingClass.value = rect.left <= 40;
  }
  
  // 计算面板大小
  const clientWidth = simpleBarRef.value?.$el?.clientWidth ?? 0;
  const calculatedSize = Math.min(clientWidth / 2, 768);
  const finalSize = calculatedSize > 0 ? calculatedSize : 400; // 如果计算失败，使用默认值 400
  
  console.log('Panel size calculation:', {
    clientWidth,
    calculatedSize,
    finalSize,
    hasSimpleBarRef: !!simpleBarRef.value,
    hasElement: !!simpleBarRef.value?.$el
  });
  
  toolPanelSize.value = finalSize;
};

// 获取分享的会话数据
const fetchSharedSession = async () => {
  try {
    loading.value = true;
    error.value = '';
    const { shareId, token } = route.params;
    if (!shareId || !token) {
      error.value = 'Invalid share link';
      return;
    }

    const session = await getSharedSession(shareId as string, token as string);
    sessionId.value = session.session_id;
    title.value = session.title || 'Shared Conversation';
    sharedAt.value = session.shared_at;
    events.value = session.events;
    
    // 从分享会话中提取文件：检查直接文件字段或事件中的附件
    let extractedFiles: FileInfo[] = [];
    
    if (session.files && session.files.length > 0) {
      extractedFiles = session.files;
    } else {
      // 从事件中的消息附件中提取文件
      const fileMap = new Map(); // 去重
      for (const event of session.events) {
        if (event.event === 'message') {
          const messageData = event.data as any;
          if (messageData.attachments && Array.isArray(messageData.attachments) && messageData.attachments.length > 0) {
            for (const attachment of messageData.attachments) {
              if (attachment.file_id && !fileMap.has(attachment.file_id)) {
                fileMap.set(attachment.file_id, attachment);
                extractedFiles.push(attachment);
              }
            }
          }
        }
      }
    }
    sharedFiles.value = extractedFiles;
    
    // 重置回放状态
    currentEventIndex.value = 0;
    displayedMessages.value = [];
    
    // 如果有事件，处理第一个事件
    if (events.value.length > 0) {
      processEventsUpToIndex(0);
    }
    
    // 延迟显示默认沙盒，确保组件已挂载
    await nextTick();
    setTimeout(() => {
      showDefaultSandbox();
      // 自动开始播放
      if (events.value.length > 0) {
        startPlayback();
      }
    }, 500);
    
  } catch (err) {
    console.error('Failed to fetch shared session:', err);
    error.value = 'Failed to load shared conversation';
  } finally {
    loading.value = false;
  }
};

// 获取最后一个步骤
const getLastStep = (): StepContent | undefined => {
  return displayedMessages.value.filter(message => message.type === 'step').pop()?.content as StepContent;
};

// 处理消息事件
const handleMessageEvent = (messageData: MessageEventData) => {
  displayedMessages.value.push({
    type: messageData.role,
    content: {
      ...messageData
    } as MessageContent,
  });

  if (messageData.attachments?.length > 0) {
    displayedMessages.value.push({
      type: 'attachments',
      content: {
        ...messageData
      } as AttachmentsContent,
    });
  }
};

// 处理工具事件
const handleToolEvent = (toolData: ToolEventData) => {
  const lastStep = getLastStep();
  let toolContent: ToolContent = {
    ...toolData
  };
  
  if (lastTool.value && lastTool.value.tool_call_id === toolContent.tool_call_id) {
    Object.assign(lastTool.value, toolContent);
  } else {
    if (lastStep?.status === 'running') {
      lastStep.tools.push(toolContent);
    } else {
      displayedMessages.value.push({
        type: 'tool',
        content: toolContent,
      });
    }
    lastTool.value = toolContent;
  }
  
  if (toolContent.name !== 'message') {
    lastNoMessageTool.value = toolContent;
    // 在回放模式下总是显示工具面板
    if (rightPanel.value) {
      rightPanel.value.showTool(toolContent, false);
    }
  }
};

// 处理步骤事件
const handleStepEvent = (stepData: StepEventData) => {
  const lastStep = getLastStep();
  if (stepData.status === 'running') {
    displayedMessages.value.push({
      type: 'step',
      content: {
        ...stepData,
        tools: []
      } as StepContent,
    });
  } else if (stepData.status === 'completed' && lastStep) {
    lastStep.status = stepData.status;
  }
};

// 处理计划事件
const handlePlanEvent = (planData: PlanEventData) => {
  plan.value = planData;
};

// 处理标题事件
const handleTitleEvent = (titleData: TitleEventData) => {
  title.value = titleData.title;
};

// 处理错误事件
const handleErrorEvent = (errorData: ErrorEventData) => {
  displayedMessages.value.push({
    type: 'assistant',
    content: {
      content: errorData.error,
      timestamp: errorData.timestamp
    } as MessageContent,
  });
};

// 处理事件到指定索引
const processEventsUpToIndex = (targetIndex: number) => {
  // 重置状态
  displayedMessages.value = [];
  plan.value = undefined;
  lastTool.value = undefined;
  lastNoMessageTool.value = undefined;
  lastMessageTool.value = undefined;
  
  // 处理到目标索引的所有事件
  for (let i = 0; i <= targetIndex && i < events.value.length; i++) {
    const event = events.value[i];
    
    switch (event.event) {
      case 'message':
        handleMessageEvent(event.data as MessageEventData);
        break;
      case 'tool':
        handleToolEvent(event.data as ToolEventData);
        break;
      case 'step':
        handleStepEvent(event.data as StepEventData);
        break;
      case 'plan':
        handlePlanEvent(event.data as PlanEventData);
        break;
      case 'title':
        handleTitleEvent(event.data as TitleEventData);
        break;
      case 'error':
        handleErrorEvent(event.data as ErrorEventData);
        break;
    }
  }
};

// 播放控制
const togglePlayback = () => {
  if (isPlaying.value) {
    stopPlayback();
  } else {
    startPlayback();
  }
};

const startPlayback = () => {
  if (events.value.length === 0) return;
  
  isPlaying.value = true;
  playbackInterval = window.setInterval(() => {
    if (currentEventIndex.value < events.value.length - 1) {
      currentEventIndex.value++;
      processEventsUpToIndex(currentEventIndex.value);
      scrollToBottom();
    } else {
      stopPlayback();
    }
  }, 1000 / Number(playbackSpeed.value));
};

const stopPlayback = () => {
  isPlaying.value = false;
  if (playbackInterval) {
    clearInterval(playbackInterval);
    playbackInterval = null;
  }
};

const stepForward = () => {
  if (currentEventIndex.value < events.value.length - 1) {
    currentEventIndex.value++;
    processEventsUpToIndex(currentEventIndex.value);
    scrollToBottom();
  }
};

const stepBackward = () => {
  if (currentEventIndex.value > 0) {
    currentEventIndex.value--;
    processEventsUpToIndex(currentEventIndex.value);
    scrollToBottom();
  }
};

const reset = () => {
  stopPlayback();
  currentEventIndex.value = 0;
  processEventsUpToIndex(0);
  scrollToTop();
};

const handleSliderChange = () => {
  stopPlayback();
  processEventsUpToIndex(currentEventIndex.value);
  scrollToBottom();
};

// 滚动控制
const scrollToBottom = async () => {
  await nextTick();
  if (simpleBarRef.value) {
    simpleBarRef.value.scrollToBottom();
  }
};

const scrollToTop = async () => {
  await nextTick();
  if (simpleBarRef.value) {
    simpleBarRef.value.scrollToTop();
  }
};

// 处理工具点击
const handleToolClick = (tool: ToolContent) => {
  if (rightPanel.value) {
    rightPanel.value.showTool(tool, false);
  }
};

// 处理文件列表显示
const handleFileListShow = () => {
  // 在回放模式下，直接使用分享会话中的文件列表
  eventBus.emit(EVENT_SESSION_FILE_LIST_SHOW, { 
    files: sharedFiles.value, 
    isPlaybackMode: true 
  });
};

// 处理滚动
const handleScroll = () => {
  // 回放模式下可能不需要特殊的滚动处理
};

// 跳转到实时
const jumpToRealTime = () => {
  // 在回放模式下不适用
};

// 显示默认沙盒面板
const showDefaultSandbox = () => {
  console.log('showDefaultSandbox called:', {
    rightPanel: !!rightPanel.value,
    sessionId: sessionId.value,
    toolPanelSize: toolPanelSize.value
  });
  
  if (rightPanel.value && sessionId.value) {
    // 创建一个默认的工具内容来显示沙盒
    const defaultToolContent: ToolContent = {
      tool_call_id: 'default-sandbox',
      name: 'run_terminal_cmd',
      status: 'called' as any,
      function: 'run_terminal_cmd',
      args: { command: 'echo "Shared conversation sandbox"' },
      content: 'Sandbox environment for shared conversation',
      timestamp: Date.now()
    };
    
    console.log('Calling rightPanel.showTool with:', defaultToolContent);
    rightPanel.value.showTool(defaultToolContent, false);
    
    // 验证面板是否显示
    setTimeout(() => {
      console.log('Panel state after showTool:', {
        isShow: rightPanel.value?.isShow,
        toolPanelSize: toolPanelSize.value
      });
    }, 100);
  } else {
    console.log('Cannot show sandbox - missing dependencies:', {
      hasRightPanel: !!rightPanel.value,
      hasSessionId: !!sessionId.value
    });
  }
};

// 格式化分享日期
const formatSharedDate = (timestamp: number) => {
  if (!timestamp) return 'Unknown';
  return new Date(timestamp * 1000).toLocaleDateString();
};

// 监听播放速度变化
watch(playbackSpeed, () => {
  if (isPlaying.value) {
    stopPlayback();
    startPlayback();
  }
});

onMounted(() => {
  fetchSharedSession();
  
  // 初始化面板大小和默认显示沙盒
  nextTick(() => {
    checkElementPosition();
    // 延迟一点再显示沙盒，确保所有初始化完成
    setTimeout(() => {
      showDefaultSandbox();
    }, 100);
  });
});

onUnmounted(() => {
  stopPlayback();
});
</script>

<style scoped>
.playback-controls {
  border: 1px solid var(--border-main);
}

.btn-playback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: var(--background-white-main);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-playback:hover:not(:disabled) {
  background: var(--fill-tsp-white-dark);
  transform: translateY(-1px);
}

.btn-playback:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-play {
  background: var(--primary-color, #007bff);
  color: white;
}

.btn-play:hover:not(:disabled) {
  background: var(--primary-color-dark, #0056b3);
}

.progress-slider {
  width: 120px;
  height: 4px;
  background: var(--background-gray-light);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.speed-select {
  padding: 4px 8px;
  border: 1px solid var(--border-main);
  border-radius: 4px;
  background: var(--background-white-main);
  color: var(--text-primary);
  font-size: 12px;
}

@keyframes bounce-dot {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.animate-bounce-dot {
  animation: bounce-dot 1.4s infinite ease-in-out both;
}
</style> 