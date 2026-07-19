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
    status: SessionStatus;
    events: AgentSSEEvent[];
    is_shared: boolean;
}

export interface ListSessionItem {
    session_id: string;
    title: string | null;
    latest_message: string | null;
    latest_message_at: number | null;
    status: SessionStatus;
    unread_message_count: number;
    is_shared: boolean;
    is_favorite: boolean;
    project_id: string | null;
}

export interface ListSessionResponse {
    sessions: ListSessionItem[];
}

export interface ProjectItem {
    project_id: string;
    name: string;
    instruction: string | null;
    is_pinned: boolean;
    sort_order: number;
}

export interface ListProjectsResponse {
    projects: ProjectItem[];
}

export interface LibraryFileItem {
    session_id: string;
    session_title: string | null;
    file_id: string | null;
    filename: string | null;
    file_path: string | null;
}

export interface LibraryResponse {
    files: LibraryFileItem[];
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

export interface SignedUrlResponse {
    signed_url: string;
    expires_in: number;
}

export interface ShareSessionResponse {
    session_id: string;
    is_shared: boolean;
}

export interface SharedSessionResponse {
    session_id: string;
    title: string | null;
    status: SessionStatus;
    events: AgentSSEEvent[];
    is_shared: boolean;
}
  