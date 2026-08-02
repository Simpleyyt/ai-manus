/**
 * Chat WebSocket — one connection per tab; switch sessions via join/leave.
 * Protocol v2: envelope (id/timestamp/version), awaitable control frames,
 * status_update, error codes — aligned with official Manus control plane.
 */
import { BASE_URL } from './client';
import type { AgentEvent, AgentStatus, StatusUpdateEventData } from '../types/event';
import type { ChatAttachment } from './agent';

export const CHAT_WS_PROTOCOL_VERSION = 2;
export const CHAT_WS_REQUEST_TIMEOUT_MS = 10_000;

export type ChatWSServerMessage =
  | { type: 'joined'; session_id: string; request_id?: string }
  | { type: 'left'; session_id: string; request_id?: string }
  | { type: 'stopped'; session_id: string; request_id?: string }
  | { type: 'ack'; request_id: string; op: string; session_id: string; ok: boolean }
  | { type: 'stream_end'; session_id: string }
  | { type: 'ping' }
  | { type: 'error'; error: string; code?: number; session_id?: string; request_id?: string }
  | { type: 'event'; session_id: string; event: string; data: AgentEvent['data'] | StatusUpdateEventData };

type EventHandler = (msg: {
  event: AgentEvent['event'] | 'status_update';
  data: AgentEvent['data'] | StatusUpdateEventData;
}) => void;

type SessionHandlers = {
  onEvent?: EventHandler;
  onOpen?: () => void;
  onStreamEnd?: () => void;
  onStatusUpdate?: (agentStatus: AgentStatus) => void;
  onError?: (error: string, code?: number) => void;
};

type PendingRequest = {
  resolve: (msg: ChatWSServerMessage) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout>;
  /** Accept these server message types as a successful response */
  expect: Set<string>;
};

function shortUID(): string {
  return `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

class ChatWebSocket {
  private ws: WebSocket | null = null;
  private closed = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private joinedSessionId: string | null = null;
  private pendingJoin: { sessionId: string; lastEventId?: string } | null = null;
  private handlers = new Map<string, SessionHandlers>();
  private readyWaiters: Array<() => void> = [];
  private pendingRequests = new Map<string, PendingRequest>();
  /** Connection generation — regenerated on each (re)connect */
  private connId = shortUID();

  connect() {
    if (this.closed) return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsBase = BASE_URL.replace(/^http/, 'ws');
    this.ws = new WebSocket(`${wsBase}/ws/chat`);

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this.connId = shortUID();
      this.readyWaiters.splice(0).forEach(resolve => resolve());
      // Re-join after reconnect
      const target = this.pendingJoin || (this.joinedSessionId
        ? { sessionId: this.joinedSessionId }
        : null);
      if (target) {
        this.joinedSessionId = null;
        void this.joinSession(target.sessionId, target.lastEventId);
      }
    };

    this.ws.onmessage = (ev) => {
      let msg: ChatWSServerMessage;
      try {
        msg = JSON.parse(ev.data) as ChatWSServerMessage;
      } catch {
        return;
      }
      this.handleMessage(msg);
    };

    this.ws.onclose = () => {
      this.ws = null;
      this.joinedSessionId = null;
      this.failAllPending('WebSocket closed');
      if (this.closed) return;
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
      this.connect();
    }, this.reconnectDelay);
  }

  private failAllPending(reason: string) {
    for (const [id, pending] of this.pendingRequests) {
      clearTimeout(pending.timer);
      pending.reject(new Error(reason));
      this.pendingRequests.delete(id);
    }
  }

  private async waitReady(): Promise<void> {
    this.connect();
    if (this.ws?.readyState === WebSocket.OPEN) return;
    await new Promise<void>((resolve) => {
      this.readyWaiters.push(resolve);
    });
  }

  private envelope(type: string, fields: Record<string, unknown> = {}): Record<string, unknown> {
    return {
      id: shortUID(),
      timestamp: Math.floor(Date.now() / 1000),
      version: CHAT_WS_PROTOCOL_VERSION,
      conn_id: this.connId,
      type,
      ...fields,
    };
  }

  private send(payload: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  /**
   * Send a control frame and wait for a matching ack / joined / stopped / error.
   */
  private async request(
    type: string,
    fields: Record<string, unknown>,
    expect: string[],
    timeoutMs = CHAT_WS_REQUEST_TIMEOUT_MS,
  ): Promise<ChatWSServerMessage> {
    await this.waitReady();
    const payload = this.envelope(type, fields);
    const requestId = String(payload.id);

    return new Promise<ChatWSServerMessage>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error(`Chat WS ${type} timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      this.pendingRequests.set(requestId, {
        resolve,
        reject,
        timer,
        expect: new Set(expect),
      });

      this.send(payload);
    });
  }

  private resolvePending(msg: ChatWSServerMessage) {
    const requestId =
      'request_id' in msg && typeof msg.request_id === 'string'
        ? msg.request_id
        : undefined;
    if (!requestId) return false;

    const pending = this.pendingRequests.get(requestId);
    if (!pending) return false;

    if (msg.type === 'error') {
      clearTimeout(pending.timer);
      this.pendingRequests.delete(requestId);
      const code = msg.code != null ? ` [${msg.code}]` : '';
      pending.reject(new Error(`${msg.error}${code}`));
      return true;
    }

    if (pending.expect.has(msg.type)) {
      clearTimeout(pending.timer);
      this.pendingRequests.delete(requestId);
      pending.resolve(msg);
      return true;
    }
    return false;
  }

  private handleMessage(msg: ChatWSServerMessage) {
    if (msg.type === 'ping') return;

    // Resolve awaitable control-frame waiters first
    if (this.resolvePending(msg)) {
      // Still apply side effects for joined / left / stopped / ack below when useful
      if (msg.type === 'ack') return;
      if (msg.type === 'error') {
        const sid = msg.session_id || this.joinedSessionId;
        if (sid) this.handlers.get(sid)?.onError?.(msg.error, msg.code);
        else console.error('Chat WS error:', msg.error, msg.code);
        return;
      }
    }

    if (msg.type === 'joined') {
      this.joinedSessionId = msg.session_id;
      this.handlers.get(msg.session_id)?.onOpen?.();
      return;
    }

    if (msg.type === 'left') {
      if (this.joinedSessionId === msg.session_id) {
        this.joinedSessionId = null;
      }
      return;
    }

    if (msg.type === 'stopped') {
      return;
    }

    if (msg.type === 'ack') {
      return;
    }

    if (msg.type === 'stream_end') {
      this.handlers.get(msg.session_id)?.onStreamEnd?.();
      return;
    }

    if (msg.type === 'error') {
      const sid = msg.session_id || this.joinedSessionId;
      if (sid) this.handlers.get(sid)?.onError?.(msg.error, msg.code);
      else console.error('Chat WS error:', msg.error, msg.code);
      return;
    }

    if (msg.type === 'event') {
      if (msg.event === 'status_update') {
        const data = msg.data as StatusUpdateEventData;
        this.handlers.get(msg.session_id)?.onStatusUpdate?.(data.agent_status);
      }
      this.handlers.get(msg.session_id)?.onEvent?.({
        event: msg.event as AgentEvent['event'] | 'status_update',
        data: msg.data,
      });
    }
  }

  setHandlers(sessionId: string, handlers: SessionHandlers) {
    this.handlers.set(sessionId, handlers);
  }

  clearHandlers(sessionId: string) {
    this.handlers.delete(sessionId);
  }

  async joinSession(sessionId: string, lastEventId?: string): Promise<void> {
    await this.waitReady();
    if (this.joinedSessionId === sessionId) {
      this.pendingJoin = { sessionId, lastEventId };
      return;
    }

    this.pendingJoin = { sessionId, lastEventId };
    if (this.joinedSessionId && this.joinedSessionId !== sessionId) {
      this.send(this.envelope('leave_session', { session_id: this.joinedSessionId }));
      this.joinedSessionId = null;
    }

    await this.request(
      'join_session',
      {
        session_id: sessionId,
        last_event_id: lastEventId,
      },
      ['joined'],
    );
  }

  async leaveSession(sessionId?: string) {
    const target = sessionId || this.joinedSessionId;
    if (!target) return;
    if (this.pendingJoin?.sessionId === target) {
      this.pendingJoin = null;
    }
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send(this.envelope('leave_session', { session_id: target }));
    }
    if (this.joinedSessionId === target) {
      this.joinedSessionId = null;
    }
  }

  async chat(params: {
    sessionId: string;
    message?: string;
    lastEventId?: string;
    attachments?: ChatAttachment[];
  }) {
    await this.waitReady();
    if (this.joinedSessionId !== params.sessionId) {
      await this.joinSession(params.sessionId, params.lastEventId);
    }
    // Await ack so caller knows the server accepted the chat frame
    await this.request(
      'chat',
      {
        session_id: params.sessionId,
        message: params.message || '',
        last_event_id: params.lastEventId,
        attachments: params.attachments || [],
      },
      ['ack'],
    );
  }

  async stopSession(sessionId: string) {
    await this.request(
      'stop_session',
      { session_id: sessionId },
      ['stopped'],
    );
  }

  destroy() {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.failAllPending('WebSocket destroyed');
    this.handlers.clear();
    this.ws?.close();
    this.ws = null;
  }
}

let singleton: ChatWebSocket | null = null;

export function getChatWebSocket(): ChatWebSocket {
  if (!singleton) {
    singleton = new ChatWebSocket();
    singleton.connect();
  }
  return singleton;
}
