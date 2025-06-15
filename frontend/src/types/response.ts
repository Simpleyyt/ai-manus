import { AgentSSEEvent } from "./event";

export enum SessionStatus {
    PENDING = "pending",
    RUNNING = "running",
    WAITING = "waiting",
    COMPLETED = "completed"
}

export interface CreateSessionResponse {
    session_id: string;
}

export interface GetSessionResponse {
    session_id: string;
    title: string | null;
    events: AgentSSEEvent[];
}

export interface ListSessionItem {
    session_id: string;
    title: string | null;
    latest_message: string | null;
    latest_message_at: number | null;
    status: SessionStatus;
    unread_message_count: number;
}

export interface ListSessionResponse {
    sessions: ListSessionItem[];
}

export interface ConsoleRecord {
    ps1: string;
    command: string;
    output: string;
  }
  
  export interface ShellViewResponse {
    output: string;
    session_id: string;
    console: ConsoleRecord[];
  }

export interface FileViewResponse {
    content: string;
    file: string;
  }
  