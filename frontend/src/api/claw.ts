import { apiClient, ApiResponse, BASE_URL } from './client';
import { getStoredToken } from './auth';

export type ClawStatus = 'creating' | 'running' | 'stopped' | 'error';

export interface Claw {
  id: string;
  user_id: string;
  status: ClawStatus;
  container_name?: string;
  error_message?: string;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClawApiKey {
  api_key: string;
}

export interface ClawEvent {
  type: 'text' | 'done' | 'error' | 'file' | 'catchup' | 'heartbeat' | 'status';
  content?: string;
  stop_reason?: string;
  error?: string;
  status?: ClawStatus;
  file_id?: string;
  filename?: string;
  content_type?: string;
  size?: number;
  upload_date?: string;
  file_url?: string;
}

export interface ClawChatAttachment {
  file_id: string;
  filename: string;
  content_type?: string;
  size: number;
  file_url?: string;
}

export interface ClawChatMessage {
  role: 'user' | 'assistant' | 'attachments';
  content: string;
  timestamp: number;
  attachments?: ClawChatAttachment[];
}

// ---- REST endpoints ----

export async function getClaw(): Promise<Claw> {
  const response = await apiClient.get<ApiResponse<Claw>>('/claw');
  return response.data.data;
}

export async function createClaw(): Promise<Claw> {
  const response = await apiClient.post<ApiResponse<Claw>>('/claw');
  return response.data.data;
}

export async function deleteClaw(): Promise<void> {
  await apiClient.delete<ApiResponse<{}>>('/claw');
}

export async function getClawApiKey(): Promise<string> {
  const response = await apiClient.get<ApiResponse<ClawApiKey>>('/claw/api-key');
  return response.data.data.api_key;
}

export async function getClawHistory(): Promise<ClawChatMessage[]> {
  const response = await apiClient.get<ApiResponse<{ messages: ClawChatMessage[] }>>('/claw/history');
  return response.data.data.messages;
}

// ---- WebSocket connection ----

export interface ClawWSCallbacks {
  onEvent: (event: ClawEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

/**
 * Manages a persistent WebSocket connection to the Claw backend.
 * Auto-reconnects on disconnect with exponential backoff.
 */
export class ClawWebSocket {
  private ws: WebSocket | null = null;
  private callbacks: ClawWSCallbacks;
  private closed = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;

  constructor(callbacks: ClawWSCallbacks) {
    this.callbacks = callbacks;
    this.connect();
  }

  private connect() {
    if (this.closed) return;

    const wsBase = BASE_URL.replace(/^http/, 'ws');
    const token = getStoredToken();
    const params = token ? `?token=${encodeURIComponent(token)}` : '';
    const url = `${wsBase}/claw/ws${params}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this.callbacks.onOpen?.();
    };

    this.ws.onmessage = (e) => {
      try {
        const data: ClawEvent = JSON.parse(e.data);
        if (data.type !== 'heartbeat') {
          this.callbacks.onEvent(data);
        }
      } catch {
        // ignore
      }
    };

    this.ws.onclose = () => {
      this.callbacks.onClose?.();
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private scheduleReconnect() {
    if (this.closed) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
      this.connect();
    }, this.reconnectDelay);
  }

  /**
   * Send a chat message through the WebSocket, optionally with file attachments.
   */
  send(message: string, sessionId: string = 'default', fileIds?: string[]) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const payload: Record<string, unknown> = { type: 'chat', message, session_id: sessionId };
      if (fileIds && fileIds.length > 0) {
        payload.file_ids = fileIds;
      }
      this.ws.send(JSON.stringify(payload));
    }
  }

  /**
   * Close the connection permanently (no auto-reconnect).
   */
  disconnect() {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
