// Backend API service
import { apiClient, API_CONFIG, ApiResponse, createSSEConnection, SSECallbacks } from './client';
import { AgentSSEEvent } from '../types/event';
import { CreateSessionResponse, GetSessionResponse, ShellViewResponse, FileViewResponse, ListSessionResponse, SignedUrlResponse, ShareSessionResponse, SharedSessionResponse } from '../types/response';
import type { FileInfo } from './file';



/**
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

export async function getSessionsSSE(callbacks?: SSECallbacks<ListSessionResponse>): Promise<() => void> {
  return createSSEConnection<ListSessionResponse>(
    '/sessions',
    {
      method: 'POST'
    },
    callbacks
  );
}

export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete<ApiResponse<void>>(`/sessions/${sessionId}`);
}

export async function stopSession(sessionId: string): Promise<void> {
  await apiClient.post<ApiResponse<void>>(`/sessions/${sessionId}/stop`);
}

/**
 * Create VNC signed URL
 * @param sessionId Session ID to create signed URL for
 * @param expireMinutes URL expiration time in minutes (default: 15)
 * @returns Signed URL response for VNC WebSocket access
 */
export async function createVncSignedUrl(sessionId: string, expireMinutes: number = 15): Promise<SignedUrlResponse> {
  const response = await apiClient.post<ApiResponse<SignedUrlResponse>>(`/sessions/${sessionId}/vnc/signed-url`, {
    expire_minutes: expireMinutes
  });
  return response.data.data;
}

/**
 * Get VNC WebSocket URL with signed URL
 * @param sessionId Session ID
 * @param expireMinutes URL expiration time in minutes (default: 60)
 * @returns Promise resolving to signed VNC WebSocket URL string
 * 
 * @example
 * // Signed URL (no Authorization header needed, more secure)
 * const url = await getVNCUrl('session123');
 * const url = await getVNCUrl('session123', 120);
 */
export const getVNCUrl = async (
  sessionId: string, 
  expireMinutes: number = 15
): Promise<string> => {
    const signedUrlResponse = await createVncSignedUrl(sessionId, expireMinutes);
    const wsBaseUrl = API_CONFIG.host.replace(/^http/, 'ws');
    return `${wsBaseUrl}${signedUrlResponse.signed_url}`;
}

/**
 * Chat with Session (using SSE to receive streaming responses)
 * @returns A function to cancel the SSE connection
 */
export const chatWithSession = async (
  sessionId: string, 
  message: string = '',
  eventId?: string,
  attachments?: string[],
  callbacks?: SSECallbacks<AgentSSEEvent['data']>
): Promise<() => void> => {
  return createSSEConnection<AgentSSEEvent['data']>(
    `/sessions/${sessionId}/chat`,
    {
      method: 'POST',
      body: { 
        message, 
        timestamp: Math.floor(Date.now() / 1000), 
        event_id: eventId,
        attachments
      }
    },
    callbacks
  );
};

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