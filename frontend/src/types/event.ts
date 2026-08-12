import type { FileInfo } from '../api/file';

/** Wire agent_status from chat WS status_update (official Manus-aligned). */
export type AgentStatus = 'pending' | 'running' | 'waiting' | 'completed' | 'error';

/** Chat / session agent event over WebSocket (and history REST payloads). */
export type AgentEvent = {
  event: 'tool' | 'step' | 'message' | 'error' | 'done' | 'title' | 'wait' | 'plan' | 'attachments' | 'status_update' | 'terminal_update' | 'file_update';
  data: ToolEventData | StepEventData | MessageEventData | ErrorEventData | DoneEventData | TitleEventData | WaitEventData | PlanEventData | StatusUpdateEventData | TerminalUpdateEventData | FileUpdateEventData;
}

export interface BaseEventData {
  event_id: string;
  timestamp: number;
}

export interface StatusUpdateEventData extends BaseEventData {
  agent_status: AgentStatus;
}

/** Official Manus ``terminalUpdate`` — live shell console push. */
export interface TerminalUpdateEventData extends BaseEventData {
  shell_id: string;
  output: unknown;
  description?: string | null;
}

/** Official text_editor / file panel content push. */
export interface FileUpdateEventData extends BaseEventData {
  path: string;
  content: string;
  old_content?: string | null;
  file?: FileInfo | null;
}

export interface ToolEventData extends BaseEventData {
  tool_call_id: string;
  name: string;
  status: "calling" | "called";
  function: string;
  args: {[key: string]: any};
  content?: any;
  /** Official StandardToolUsed timeline label (NL action), not file path. */
  brief?: string | null;
}

export interface StepEventData extends BaseEventData {
  status: "pending" | "running" | "completed" | "failed"
  id: string
  description: string
  /** Present when the step finished with a concrete outcome. */
  result?: string
}

export interface MessageEventData extends BaseEventData {
  content: string;
  role: "user" | "assistant";
  attachments: FileInfo[];
}

export interface ErrorEventData extends BaseEventData {
  error: string;
}

export type DoneEventData = BaseEventData

export type WaitEventData = BaseEventData

export interface TitleEventData extends BaseEventData {
  title: string;
}

export interface PlanEventData extends BaseEventData {
  steps: StepEventData[];
}
