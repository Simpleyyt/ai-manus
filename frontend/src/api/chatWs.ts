/**
 * Chat WebSocket — one connection per tab; switch sessions via join/leave.
 * Aligns with official Manus join_session / leave_session pattern.
 */
import { BASE_URL } from './client';
import type { AgentSSEEvent } from '../types/event';
import type { ChatAttachment } from './agent';

export type ChatWSServerMessage =
  | { type: 'joined'; session_id: string }
  | { type: 'left'; session_id: string }
  | { type: 'stopped'; session_id: string }
  | { type: 'stream_end'; session_id: string }
  | { type: 'ping' }
  | { type: 'error'; error: string; session_id?: string }
  | { type: 'event'; session_id: string; event: string; data: AgentSSEEvent['data'] };

type EventHandler = (msg: {
  event: AgentSSEEvent['event'];
  data: AgentSSEEvent['data'];
}) => void;

type SessionHandlers = {
  onEvent?: EventHandler;
  onOpen?: () => void;
  onStreamEnd?: () => void;
  onError?: (error: string) => void;
};

class ChatWebSocket {
  private ws: WebSocket | null = null;
  private closed = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private joinedSessionId: string | null = null;
  private pendingJoin: { sessionId: string; lastEventId?: string } | null = null;
  private handlers = new Map<string, SessionHandlers>();
  private readyWaiters: Array<() => void> = [];
  private joinWaiters = new Map<string, Array<(ok: boolean, error?: string) => void>>();

  connect() {
    if (this.closed) return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsBase = BASE_URL.replace(/^http/, 'ws');
    this.ws = new WebSocket(`${wsBase}/ws/chat`);

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this.readyWaiters.splice(0).forEach(resolve => resolve());
      // Re-join after reconnect
      const target = this.pendingJoin || (this.joinedSessionId
        ? { sessionId: this.joinedSessionId }
        : null);
      if (target) {
        // Clear local join state; wait for server ack via joinSession path below
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
      // Fail pending join waiters so callers don't hang
      for (const [sid, waiters] of this.joinWaiters) {
        waiters.forEach(w => w(false, 'WebSocket closed'));
        this.joinWaiters.delete(sid);
      }
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

  private async waitReady(): Promise<void> {
    this.connect();
    if (this.ws?.readyState === WebSocket.OPEN) return;
    await new Promise<void>((resolve) => {
      this.readyWaiters.push(resolve);
    });
  }

  private send(payload: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  private resolveJoinWaiters(sessionId: string, ok: boolean, error?: string) {
    const waiters = this.joinWaiters.get(sessionId);
    if (!waiters?.length) return;
    this.joinWaiters.delete(sessionId);
    waiters.forEach(w => w(ok, error));
  }

  private handleMessage(msg: ChatWSServerMessage) {
    if (msg.type === 'ping') return;

    if (msg.type === 'joined') {
      this.joinedSessionId = msg.session_id;
      this.resolveJoinWaiters(msg.session_id, true);
      this.handlers.get(msg.session_id)?.onOpen?.();
      return;
    }

    if (msg.type === 'left') {
      if (this.joinedSessionId === msg.session_id) {
        this.joinedSessionId = null;
      }
      return;
    }

    if (msg.type === 'stream_end') {
      this.handlers.get(msg.session_id)?.onStreamEnd?.();
      return;
    }

    if (msg.type === 'error') {
      const sid = msg.session_id || this.joinedSessionId;
      if (sid && this.joinWaiters.has(sid)) {
        this.resolveJoinWaiters(sid, false, msg.error);
      }
      if (sid) this.handlers.get(sid)?.onError?.(msg.error);
      else console.error('Chat WS error:', msg.error);
      return;
    }

    if (msg.type === 'event') {
      this.handlers.get(msg.session_id)?.onEvent?.({
        event: msg.event as AgentSSEEvent['event'],
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
      this.send({ type: 'leave_session', session_id: this.joinedSessionId });
      this.joinedSessionId = null;
    }

    const joined = new Promise<void>((resolve, reject) => {
      const waiters = this.joinWaiters.get(sessionId) || [];
      waiters.push((ok, error) => {
        if (ok) resolve();
        else reject(new Error(error || 'Failed to join session'));
      });
      this.joinWaiters.set(sessionId, waiters);
    });

    this.send({
      type: 'join_session',
      session_id: sessionId,
      last_event_id: lastEventId,
    });

    await joined;
  }

  async leaveSession(sessionId?: string) {
    const target = sessionId || this.joinedSessionId;
    if (!target) return;
    if (this.pendingJoin?.sessionId === target) {
      this.pendingJoin = null;
    }
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({ type: 'leave_session', session_id: target });
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
    this.send({
      type: 'chat',
      session_id: params.sessionId,
      message: params.message || '',
      last_event_id: params.lastEventId,
      timestamp: Math.floor(Date.now() / 1000),
      attachments: params.attachments || [],
    });
  }

  async stopSession(sessionId: string) {
    await this.waitReady();
    this.send({ type: 'stop_session', session_id: sessionId });
  }

  destroy() {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
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
