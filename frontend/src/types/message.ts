import type { FileInfo } from '../api/file';

export type MessageType = "user" | "assistant" | "tool" | "step" | "attachments";

export interface Message {
  type: MessageType;
  content: BaseContent;
}

export interface BaseContent {
  timestamp: number;
}

export interface MessageContent extends BaseContent {
  content: string;
  /** User-turn attachments rendered above the text bubble (official ChatQuestion). */
  attachments?: FileInfo[];
}

export interface ToolContent extends BaseContent {
  tool_call_id: string;
  name: string;
  function: string;
  args: any;
  content?: any;
  status: "calling" | "called";
  /** Official StandardToolUsed prefers brief over path/args in the timeline. */
  brief?: string | null;
}

export interface StepContent extends BaseContent {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  tools: ToolContent[];
  /** Step outcome text shown under the StepGroup timeline (official nested chat). */
  result?: string;
}

export interface AttachmentsContent extends BaseContent {
  role: "user" | "assistant";
  attachments: FileInfo[];
}

export function isConsecutiveAssistant(messages: Message[], index: number): boolean {
  if (index <= 0) return false;
  const isAst = (m: Message) =>
    m.type === 'assistant' ||
    (m.type === 'attachments' && (m.content as AttachmentsContent).role === 'assistant');
  return isAst(messages[index]) && isAst(messages[index - 1]);
}

/** Official StepGroup shell: pb-0 when the next list item is also a stepGroup. */
export function isStepConnectedToNext(messages: Message[], index: number): boolean {
  return messages[index]?.type === 'step' && messages[index + 1]?.type === 'step';
}

/**
 * Official StepGroup `resolveVisibility` (mined rk):
 * - precedingItems = everything before the last toolUsed/chat-like row
 * - lastToolItems = from that last row to the end
 * - collapsedVisibleItems = lastToolItems only while the step is live (running);
 *   completed collapsed steps hide the body (header only)
 * - expanded → preceding + last (= all)
 */
export type StepTimelineItem =
  | { kind: 'tool'; tool: ToolContent; id: string }
  | { kind: 'result'; text: string; id: string };

export function resolveStepTimelineVisibility(step: StepContent): {
  precedingItems: StepTimelineItem[];
  lastToolItems: StepTimelineItem[];
  /** Items still shown when the step header is collapsed. */
  collapsedVisibleItems: StepTimelineItem[];
  canToggle: boolean;
} {
  const tools = step.tools ?? [];
  const result = (step.result || '').trim();
  const items: StepTimelineItem[] = [
    ...tools.map((tool, i) => ({
      kind: 'tool' as const,
      tool,
      id: tool.tool_call_id || `tool-${i}`,
    })),
  ];
  if (result) {
    items.push({ kind: 'result', text: result, id: `result-${step.id}` });
  }

  // Last toolUsed | chat (result) from the end — same scan as official.
  let lastStart = items.length;
  for (let i = items.length - 1; i >= 0; i -= 1) {
    const it = items[i];
    if (it.kind === 'tool' || it.kind === 'result') {
      lastStart = i;
      break;
    }
  }
  if (lastStart === items.length) {
    lastStart = Math.max(0, items.length - 1);
  }

  const precedingItems = items.slice(0, lastStart);
  const lastToolItems = items.slice(lastStart);
  const live = step.status === 'running';
  const collapsedVisibleItems = live ? lastToolItems : [];
  const collapsedIds = new Set(collapsedVisibleItems.map((i) => i.id));
  const canToggle = items.some((i) => !collapsedIds.has(i.id));

  return { precedingItems, lastToolItems, collapsedVisibleItems, canToggle };
}

/** Last assistant bubble before the next user turn (end of a completed turn). */
export function isAssistantLastBeforeUser(messages: Message[], index: number): boolean {
  if (messages[index]?.type !== 'assistant') return false;
  for (let i = index + 1; i < messages.length; i++) {
    const t = messages[i].type;
    if (t === 'user') return true;
    if (t === 'assistant') return false;
  }
  return false;
}

/**
 * Official ChatReplyActions: hide Copy on the last chat message when the
 * TaskCompleted / WaitingContinue footer owns it, or while the agent is live.
 * All earlier assistant replies with text keep an inline Copy.
 */
export function shouldShowAssistantCopyActions(
  messages: Message[],
  index: number,
  lastAssistantIndex: number,
  options?: { footerOwnsLastCopy?: boolean; hideLastWhileBusy?: boolean },
): boolean {
  const m = messages[index];
  if (m?.type !== 'assistant') return false;
  if (!((m.content as MessageContent).content || '').trim()) return false;
  if (index === lastAssistantIndex) {
    if (options?.footerOwnsLastCopy || options?.hideLastWhileBusy) return false;
    return true;
  }
  return true;
}
