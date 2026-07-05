import type { Ref } from 'vue';
import {
  Message,
  MessageContent,
  ToolContent,
  StepContent,
  AttachmentsContent,
} from '../types/message';
import {
  StepEventData,
  ToolEventData,
  MessageEventData,
  ErrorEventData,
  TitleEventData,
  PlanEventData,
  AgentSSEEvent,
} from '../types/event';

export interface AgentEventState {
  messages: Ref<Message[]>;
  title: Ref<string>;
  plan: Ref<PlanEventData | undefined>;
  isLoading: Ref<boolean>;
  lastEventId: Ref<string | undefined>;
  lastTool: Ref<ToolContent | undefined>;
  lastNoMessageTool: Ref<ToolContent | undefined>;
}

export interface AgentEventOptions {
  /** Called when a non-message tool is created or updated, so the page can surface it (e.g. in the tool panel). */
  onToolActivity?: (tool: ToolContent) => void;
}

/**
 * Shared conversion of agent SSE events into the UI message list.
 * Used by both ChatPage (live chat) and SharePage (replay).
 */
export function useAgentEvents(state: AgentEventState, options: AgentEventOptions = {}) {
  const { messages, title, plan, isLoading, lastEventId, lastTool, lastNoMessageTool } = state;

  const getLastStep = (): StepContent | undefined => {
    return messages.value.filter(message => message.type === 'step').pop()?.content as StepContent;
  };

  const handleMessageEvent = (messageData: MessageEventData) => {
    messages.value.push({
      type: messageData.role,
      content: {
        ...messageData
      } as MessageContent,
    });

    if (messageData.attachments && messageData.attachments.length > 0) {
      messages.value.push({
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
    if (lastTool.value && lastTool.value.tool_call_id === toolContent.tool_call_id) {
      Object.assign(lastTool.value, toolContent);
    } else {
      if (lastStep?.status === 'running') {
        lastStep.tools.push(toolContent);
      } else {
        messages.value.push({
          type: 'tool',
          content: toolContent,
        });
      }
      lastTool.value = toolContent;
    }
    if (toolContent.name !== 'message') {
      lastNoMessageTool.value = toolContent;
      options.onToolActivity?.(toolContent);
    }
  };

  const handleStepEvent = (stepData: StepEventData) => {
    const lastStep = getLastStep();
    if (stepData.status === 'running') {
      messages.value.push({
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
      isLoading.value = false;
    }
  };

  const handleErrorEvent = (errorData: ErrorEventData) => {
    isLoading.value = false;
    messages.value.push({
      type: 'assistant',
      content: {
        content: errorData.error,
        timestamp: errorData.timestamp
      } as MessageContent,
    });
  };

  const handleTitleEvent = (titleData: TitleEventData) => {
    title.value = titleData.title;
  };

  const handlePlanEvent = (planData: PlanEventData) => {
    plan.value = planData;
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
    lastEventId.value = event.data.event_id;
  };

  return { handleEvent };
}
