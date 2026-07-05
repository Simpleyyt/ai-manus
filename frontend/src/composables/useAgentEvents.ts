import { reactive, toRefs, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
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

export interface AgentEventsOptions {
  /**
   * Whether tool views may go live (auto-refreshing). Real chat sessions
   * support live tools; shared session replays never do.
   */
  liveTools?: boolean;
  /** Bridge to the page's ToolPanel component. */
  showToolPanel?: (tool: ToolContent, live: boolean) => void;
  /** Called when messages change while follow mode is enabled. */
  scrollToBottom?: () => void;
}

/**
 * Shared agent SSE event handling used by both ChatPage and SharePage.
 *
 * Owns the message list, plan, title and tool tracking state, and turns the
 * agent SSE event stream (message/tool/step/error/title/plan) into UI state.
 * Page-specific concerns (sending messages, sharing, replay) stay in pages.
 *
 * State is local to each call, not module-global.
 */
export function useAgentEvents(options: AgentEventsOptions = {}) {
  const { t } = useI18n();

  const createInitialState = () => ({
    isLoading: false,
    messages: [] as Message[],
    realTime: true,
    follow: true,
    title: t('New Chat'),
    plan: undefined as PlanEventData | undefined,
    lastNoMessageTool: undefined as ToolContent | undefined,
    lastTool: undefined as ToolContent | undefined,
    lastEventId: undefined as string | undefined,
  });

  const state = reactive(createInitialState());

  // Auto-scroll to bottom on new messages while follow mode is on
  watch(() => state.messages, async () => {
    await nextTick();
    if (state.follow) {
      options.scrollToBottom?.();
    }
  }, { deep: true });

  const getLastStep = (): StepContent | undefined => {
    return state.messages.filter(message => message.type === 'step').pop()?.content as StepContent;
  };

  const handleMessageEvent = (messageData: MessageEventData) => {
    state.messages.push({
      type: messageData.role,
      content: {
        ...messageData
      } as MessageContent,
    });

    if (messageData.attachments?.length > 0) {
      state.messages.push({
        type: 'attachments',
        content: {
          ...messageData
        } as AttachmentsContent,
      });
    }
  };

  const handleToolEvent = (toolData: ToolEventData) => {
    const lastStep = getLastStep();
    const toolContent: ToolContent = {
      ...toolData
    };
    if (state.lastTool && state.lastTool.tool_call_id === toolContent.tool_call_id) {
      Object.assign(state.lastTool, toolContent);
    } else {
      if (lastStep?.status === 'running') {
        lastStep.tools.push(toolContent);
      } else {
        state.messages.push({
          type: 'tool',
          content: toolContent,
        });
      }
      state.lastTool = toolContent;
    }
    if (toolContent.name !== 'message') {
      state.lastNoMessageTool = toolContent;
      if (state.realTime) {
        options.showToolPanel?.(toolContent, !!options.liveTools);
      }
    }
  };

  const handleStepEvent = (stepData: StepEventData) => {
    const lastStep = getLastStep();
    if (stepData.status === 'running') {
      state.messages.push({
        type: 'step',
        content: {
          ...stepData,
          tools: []
        } as StepContent,
      });
    } else if (stepData.status === 'completed') {
      if (lastStep) {
        lastStep.status = stepData.status;
      }
    } else if (stepData.status === 'failed') {
      state.isLoading = false;
    }
  };

  const handleErrorEvent = (errorData: ErrorEventData) => {
    state.isLoading = false;
    state.messages.push({
      type: 'assistant',
      content: {
        content: errorData.error,
        timestamp: errorData.timestamp
      } as MessageContent,
    });
  };

  const handleTitleEvent = (titleData: TitleEventData) => {
    state.title = titleData.title;
  };

  const handlePlanEvent = (planData: PlanEventData) => {
    state.plan = planData;
  };

  const handleEvent = (event: AgentSSEEvent) => {
    if (event.event === 'message') {
      handleMessageEvent(event.data as MessageEventData);
    } else if (event.event === 'tool') {
      handleToolEvent(event.data as ToolEventData);
    } else if (event.event === 'step') {
      handleStepEvent(event.data as StepEventData);
    } else if (event.event === 'done') {
      // Loading state is cleared when the SSE connection closes
    } else if (event.event === 'wait') {
      // TODO: handle wait event
    } else if (event.event === 'error') {
      handleErrorEvent(event.data as ErrorEventData);
    } else if (event.event === 'title') {
      handleTitleEvent(event.data as TitleEventData);
    } else if (event.event === 'plan') {
      handlePlanEvent(event.data as PlanEventData);
    }
    state.lastEventId = event.data.event_id;
  };

  /** Reset all event-derived state back to its initial values. */
  const resetEvents = () => {
    Object.assign(state, createInitialState());
  };

  const isLastNoMessageTool = (tool: ToolContent) => {
    return tool.tool_call_id === state.lastNoMessageTool?.tool_call_id;
  };

  /** A tool is "live" when it is still running or was updated recently. */
  const isLiveTool = (tool: ToolContent) => {
    if (!options.liveTools) {
      return false;
    }
    if (tool.status === 'calling') {
      return true;
    }
    if (!isLastNoMessageTool(tool)) {
      return false;
    }
    return tool.timestamp > Date.now() - 5 * 60 * 1000;
  };

  const handleToolClick = (tool: ToolContent) => {
    state.realTime = false;
    options.showToolPanel?.(tool, isLiveTool(tool));
  };

  const jumpToRealTime = () => {
    state.realTime = true;
    if (state.lastNoMessageTool) {
      options.showToolPanel?.(state.lastNoMessageTool, isLiveTool(state.lastNoMessageTool));
    }
  };

  return {
    ...toRefs(state),
    handleEvent,
    resetEvents,
    isLiveTool,
    handleToolClick,
    jumpToRealTime,
  };
}
