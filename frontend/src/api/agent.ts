// Backend API service
import { apiClient, ApiResponse, BASE_URL } from './client';
import { AgentSSEEvent } from '../types/event';
import type { AgentStatus } from '../types/event';
import { CreateSessionResponse, GetSessionResponse, ShellViewResponse, FileViewResponse, ListSessionResponse, ListSessionItem, ShareSessionResponse, SharedSessionResponse } from '../types/response';
import type { FileInfo } from './file';

export type ChatStreamCallbacks = {
  onOpen?: () => void;
  onMessage?: (event: { event: string; data: AgentSSEEvent['data'] }) => void;
  onStatusUpdate?: (agentStatus: AgentStatus) => void;
  onClose?: () => void;
  onError?: (error: Error) => void;
};/**
 * Create Session
 * @returns Session
 */
export async function createSession(): Promise<CreateSessionResponse> {
  const response = await apiClient.put<ApiResponse<CreateSessionResponse>>('/sessions');
  return response.data.data;
}

export async function getSession(sessionId: string): Promise<GetSessionResponse> {
  const response = await apiClient.get<ApiResponse<GetSessionResponse>>(`/sessions/${sessionId}`);
  return response.data.data;
}

export async function getSessions(): Promise<ListSessionResponse> {
  const response = await apiClient.get<ApiResponse<ListSessionResponse>>('/sessions');
  return response.data.data;
}

/** Session list realtime WS. */
export type SessionsListWSMessage =
  | { op: 'snapshot'; sessions: ListSessionItem[] }
  | { op: 'upsert'; session: ListSessionItem }
  | { op: 'remove'; session_id: string }
  | { op: 'ping' };

export function connectSessionsListWS(handlers: {
  onMessage: (msg: SessionsListWSMessage) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}): () => void {
  const wsBase = BASE_URL.replace(/^http/, 'ws');
  // Browser Cookie auth (B1); no ?token=
  const url = `${wsBase}/ws/sessions`;
  let closed = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectDelay = 1000;
  let ws: WebSocket | null = null;

  const clearTimer = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const connect = () => {
    if (closed) return;
    ws = new WebSocket(url);
    ws.onopen = () => {
      reconnectDelay = 1000;
    };
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as SessionsListWSMessage;
        if (msg.op === 'ping') return;
        handlers.onMessage(msg);
      } catch (e) {
        console.error('Failed to parse sessions WS message', e);
      }
    };
    ws.onerror = (err) => {
      handlers.onError?.(err);
    };
    ws.onclose = () => {
      handlers.onClose?.();
      if (closed) return;
      clearTimer();
      reconnectTimer = setTimeout(() => {
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
        connect();
      }, reconnectDelay);
    };
  };

  connect();

  return () => {
    closed = true;
    clearTimer();
    ws?.close();
    ws = null;
  };
}

export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete<ApiResponse<void>>(`/sessions/${sessionId}`);
}

export async function updateSessionTitle(sessionId: string, title: string): Promise<{ session_id: string; title: string }> {
  const response = await apiClient.patch<ApiResponse<{ session_id: string; title: string }>>(
    `/sessions/${sessionId}/title`,
    { title }
  );
  return response.data.data;
}

export async function favoriteSession(sessionId: string): Promise<{ session_id: string; is_favorite: boolean }> {
  const response = await apiClient.post<ApiResponse<{ session_id: string; is_favorite: boolean }>>(
    `/sessions/${sessionId}/favorite`
  );
  return response.data.data;
}

export async function unfavoriteSession(sessionId: string): Promise<{ session_id: string; is_favorite: boolean }> {
  const response = await apiClient.delete<ApiResponse<{ session_id: string; is_favorite: boolean }>>(
    `/sessions/${sessionId}/favorite`
  );
  return response.data.data;
}

export async function pinSession(sessionId: string, isPinned: boolean): Promise<{ session_id: string; is_pinned: boolean }> {
  const response = await apiClient.post<ApiResponse<{ session_id: string; is_pinned: boolean }>>(
    `/sessions/${sessionId}/pin`,
    { is_pinned: isPinned }
  );
  return response.data.data;
}

export async function moveSessionProject(
  sessionId: string,
  projectId: string | null
): Promise<{ session_id: string; project_id: string | null }> {
  const response = await apiClient.patch<ApiResponse<{ session_id: string; project_id: string | null }>>(
    `/sessions/${sessionId}/project`,
    { project_id: projectId }
  );
  return response.data.data;
}

export async function stopSession(sessionId: string): Promise<void> {
  try {
    const { getChatWebSocket } = await import('./chatWs');
    await getChatWebSocket().stopSession(sessionId);
  } catch {
    await apiClient.post<ApiResponse<void>>(`/sessions/${sessionId}/stop`);
  }
}

/**
 * VNC WebSocket URL — Cookie / Bearer auth (same as /ws/*). No signed URL.
 */
export const getVNCUrl = (sessionId: string): string => {
  const wsBase = BASE_URL.replace(/^http/, 'ws');
  return `${wsBase}/ws/vnc/${sessionId}`;
};

/**
 * File attachment reference sent with a chat request.
 * Mirrors the backend `ChatAttachment` schema.
 */
export interface ChatAttachment {
  file_id: string;
  filename: string;
}

/**
 * Chat with Session over persistent chat WS (join/leave).
 * Returns a cancel function that clears handlers for this call (does not close WS).
 */
export const chatWithSession = async (
  sessionId: string,
  message: string = '',
  eventId?: string,
  attachments?: ChatAttachment[],
  callbacks?: ChatStreamCallbacks
): Promise<() => void> => {
  const { getChatWebSocket } = await import('./chatWs');
  const ws = getChatWebSocket();

  ws.setHandlers(sessionId, {
    onOpen: () => callbacks?.onOpen?.(),
    onEvent: ({ event, data }) => {
      // status_update is delivered via onStatusUpdate; skip duplicate onMessage
      if (event === 'status_update') return;
      callbacks?.onMessage?.({ event, data: data as AgentSSEEvent['data'] });
    },
    onStatusUpdate: (agentStatus) => {
      callbacks?.onStatusUpdate?.(agentStatus);
    },
    onStreamEnd: () => {
      callbacks?.onClose?.();
    },
    onError: (error) => {
      callbacks?.onError?.(new Error(error));
    },
  });

  if (message || (attachments && attachments.length > 0)) {
    await ws.chat({
      sessionId,
      message,
      lastEventId: eventId,
      attachments,
    });
  } else {
    // Resume / catch-up stream for running session
    await ws.joinSession(sessionId, eventId);
  }

  return () => {
    ws.clearHandlers(sessionId);
  };
};

/** Leave chat session subscription (switch away). */
export async function leaveChatSession(sessionId: string): Promise<void> {
  const { getChatWebSocket } = await import('./chatWs');
  const ws = getChatWebSocket();
  ws.clearHandlers(sessionId);
  await ws.leaveSession(sessionId);
}

/**
 * View Shell session output
 * @param sessionId Session ID
 * @param shellSessionId Shell session ID
 * @returns Shell session output content
 */
export async function viewShellSession(sessionId: string, shellSessionId: string): Promise<ShellViewResponse> {
  const response = await apiClient.post<ApiResponse<ShellViewResponse>>(
    `/sessions/${sessionId}/shell`,
    { session_id: shellSessionId }
  );
  return response.data.data;
}

/**
 * View file content
 * @param sessionId Session ID
 * @param file File path
 * @returns File content
 */
export async function viewFile(sessionId: string, file: string): Promise<FileViewResponse> {
  const response = await apiClient.post<ApiResponse<FileViewResponse>>(
    `/sessions/${sessionId}/file`,
    { file }
  );
  return response.data.data;
}

export async function getSessionFiles(sessionId: string): Promise<FileInfo[]> {
  const response = await apiClient.get<ApiResponse<FileInfo[]>>(`/sessions/${sessionId}/files`);
  return response.data.data;
}

export async function clearUnreadMessageCount(sessionId: string): Promise<void> {
  await apiClient.post<ApiResponse<void>>(`/sessions/${sessionId}/clear_unread_message_count`);
}

/**
 * Share a session to make it publicly accessible
 * @param sessionId Session ID to share
 * @returns Share session response with current sharing status
 * 
 * @example
 * ```typescript
 * // Share a session
 * const result = await shareSession('session123');
 * console.log(result.is_shared); // true
 * ```
 */
export async function shareSession(sessionId: string): Promise<ShareSessionResponse> {
  const response = await apiClient.post<ApiResponse<ShareSessionResponse>>(`/sessions/${sessionId}/share`);
  return response.data.data;
}

/**
 * Unshare a session to make it private again
 * @param sessionId Session ID to unshare
 * @returns Share session response with current sharing status
 * 
 * @example
 * ```typescript
 * // Unshare a session
 * const result = await unshareSession('session123');
 * console.log(result.is_shared); // false
 * ```
 */
export async function unshareSession(sessionId: string): Promise<ShareSessionResponse> {
  const response = await apiClient.delete<ApiResponse<ShareSessionResponse>>(`/sessions/${sessionId}/share`);
  return response.data.data;
}

/**
 * Get a shared session without authentication
 * This endpoint allows public access to sessions that have been marked as shared.
 * No authentication token is required.
 * 
 * @param sessionId Session ID to retrieve
 * @returns Shared session data (accessible publicly)
 * 
 * @example
 * ```typescript
 * // Get a shared session (no auth required)
 * try {
 *   const sharedSession = await getSharedSession('session123');
 *   console.log(sharedSession.title);
 *   console.log(sharedSession.events);
 * } catch (error) {
 *   console.error('Session not found or not shared');
 * }
 * ```
 */
export async function getSharedSession(sessionId: string): Promise<SharedSessionResponse> {
  const response = await apiClient.get<ApiResponse<SharedSessionResponse>>(`/sessions/shared/${sessionId}`);
  return response.data.data;
}

export async function getSharedSessionFiles(sessionId: string): Promise<FileInfo[]> {
  const response = await apiClient.get<ApiResponse<FileInfo[]>>(`/sessions/${sessionId}/share/files`);
  return response.data.data;
}