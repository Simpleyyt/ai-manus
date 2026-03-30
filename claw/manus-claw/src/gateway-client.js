import WebSocket from 'ws';
import { loadOrCreateDeviceIdentity, buildDeviceAuthField } from './device-identity.js';

const LIVENESS_PING_INTERVAL_MS = 15000;
const LIVENESS_CHECK_INTERVAL_MS = 5000;
const LIVENESS_TIMEOUT_MS = 60000;
const CONNECT_TIMEOUT_MS = 15000;

export class GatewayClient {
  constructor({ url, token, agentId, logger, retry, onMessage, onReady, onClose }) {
    this.url = url;
    this.token = token;
    this.agentId = agentId || 'main';
    this.logger = logger;
    this.retry = retry || { baseMs: 1000, maxMs: 60000, maxAttempts: 0 };
    this.onMessage = onMessage;
    this.onReady = onReady;
    this.onClose = onClose;

    this.ws = null;
    this.ready = false;
    this.closing = false;
    this.backoffMs = this.retry.baseMs;
    this.attempts = 0;
    this.reconnectTimer = null;
    this.connectTimer = null;
    this.livenessPingTimer = null;
    this.livenessCheckTimer = null;
    this.lastSeenAt = 0;
    this._reqId = 0;
    this._pendingRequests = new Map();

    // Handshake state
    this._connectSent = false;
    this._connectNonce = null;
  }

  start() {
    this.closing = false;
    this.connect();
  }

  stop() {
    this.closing = true;
    this.ready = false;
    this._stopLiveness();
    this._clearConnectTimer();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try { this.ws.close(); } catch {}
      this.ws = null;
    }
  }

  isReady() {
    return this.ready;
  }

  send(frame) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !this.ready) {
      return false;
    }
    try {
      this.ws.send(JSON.stringify(frame));
      return true;
    } catch (e) {
      this.logger?.warn?.(`[gateway] send failed: ${String(e)}`);
      return false;
    }
  }

  /**
   * Send a request and wait for response
   */
  request(method, params, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      if (!this.ready) {
        return reject(new Error('Gateway not ready'));
      }
      const id = `req_${++this._reqId}`;
      const timer = setTimeout(() => {
        this._pendingRequests.delete(id);
        reject(new Error(`Request timeout: ${method}`));
      }, timeoutMs);

      this._pendingRequests.set(id, { resolve, reject, timer });
      const sent = this.send({ type: 'req', id, method, params });
      if (!sent) {
        clearTimeout(timer);
        this._pendingRequests.delete(id);
        reject(new Error('Failed to send request'));
      }
    });
  }

  connect() {
    if (this.closing) return;

    this.logger?.info?.(`[gateway] connecting to ${this.url}`);
    this.ws = new WebSocket(this.url);

    this.ws.on('open', () => {
      this._markSeen();
      this._startLiveness();
      this.backoffMs = this.retry.baseMs;
      this.attempts = 0;
      this.logger?.info?.('[gateway] connected');
      // Queue connect handshake after a short delay
      this._queueConnect();
    });

    this.ws.on('message', (data) => {
      this._markSeen();
      const raw = data.toString();

      if (raw.trim().toLowerCase() === 'ping') {
        try { this.ws?.send('pong'); } catch {}
        return;
      }
      if (raw.trim().toLowerCase() === 'pong') return;

      let msg;
      try { msg = JSON.parse(raw); } catch {
        this.logger?.warn?.('[gateway] invalid json payload');
        return;
      }

      // Handle connect challenge event (server requests nonce-signed connect)
      if (msg.type === 'event' && msg.event === 'connect.challenge') {
        const nonce = msg.payload?.nonce;
        if (typeof nonce === 'string') {
          this._connectNonce = nonce;
        }
        this._sendConnect('challenge');
        return;
      }

      // Handle connect handshake response
      if (msg.type === 'res' && msg.id === 'connect') {
        this._handleConnectResponse(msg);
        return;
      }

      // Once ready, handle responses to pending requests
      if (msg.id && this._pendingRequests.has(msg.id)) {
        const { resolve, reject, timer } = this._pendingRequests.get(msg.id);
        clearTimeout(timer);
        this._pendingRequests.delete(msg.id);
        if (msg.error) {
          reject(new Error(msg.error.message || 'RPC error'));
        } else {
          resolve(msg.result);
        }
        return;
      }

      // Forward other messages only once handshake is complete
      if (this.ready) {
        this.onMessage?.(msg);
      }
    });

    this.ws.on('close', (code, reason) => {
      this.ready = false;
      this._stopLiveness();
      this._clearConnectTimer();
      this.logger?.warn?.(`[gateway] closed code=${code} reason=${reason.toString()}`);
      this.onClose?.();
      this._scheduleReconnect();
    });

    this.ws.on('error', (err) => {
      this.logger?.warn?.(`[gateway] error: ${String(err)}`);
    });
  }

  _queueConnect() {
    this._connectSent = false;
    this._connectNonce = null;
    this._clearConnectTimer();
    // Wait a brief moment for potential challenge event before sending connect
    this.connectTimer = setTimeout(() => {
      this._sendConnect('timer');
    }, 750);
    this.connectTimer.unref?.();
  }

  _sendConnect(trigger) {
    if (this._connectSent) return;
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    this._connectSent = true;
    this._clearConnectTimer();

    const clientId = 'gateway-client';
    const clientMode = 'backend';
    const role = 'operator';
    const scopes = ['operator.admin', 'operator.read', 'operator.write'];

    const params = {
      minProtocol: 3,
      maxProtocol: 3,
      client: {
        id: clientId,
        version: '1.0.0',
        platform: process.platform,
        mode: clientMode,
        displayName: 'manus-bridge-connector',
      },
      role,
      scopes,
      caps: ['tool-events'],
    };

    if (this.token) {
      params.auth = { token: this.token };
    }

    try {
      const identity = loadOrCreateDeviceIdentity();
      params.device = buildDeviceAuthField({
        identity,
        clientId,
        clientMode,
        role,
        scopes,
        token: this.token,
        nonce: this._connectNonce || undefined,
      });
    } catch (e) {
      this.logger?.warn?.(`[gateway] device auth build failed: ${String(e)}`);
    }

    const frame = { type: 'req', id: 'connect', method: 'connect', params };
    this.logger?.info?.(`[gateway] sending connect handshake (trigger=${trigger})`);

    try {
      this.ws.send(JSON.stringify(frame));
    } catch (e) {
      this.logger?.warn?.(`[gateway] connect send failed: ${String(e)}`);
    }

    // Set a timeout for the connect response
    this._connectTimeoutTimer = setTimeout(() => {
      if (!this.ready) {
        this.logger?.warn?.('[gateway] connect handshake timed out, closing');
        try { this.ws?.close(1008, 'connect timeout'); } catch {}
      }
    }, CONNECT_TIMEOUT_MS);
    this._connectTimeoutTimer.unref?.();
  }

  _handleConnectResponse(msg) {
    if (this._connectTimeoutTimer) {
      clearTimeout(this._connectTimeoutTimer);
      this._connectTimeoutTimer = null;
    }

    if (!msg.ok) {
      const errMsg = msg.error?.message || 'handshake rejected';
      this.logger?.error?.(`[gateway] handshake rejected: ${errMsg}`);
      try { this.ws?.close(1008, 'handshake rejected'); } catch {}
      return;
    }

    this.ready = true;
    this.logger?.info?.('[gateway] handshake complete, gateway ready');
    this.onReady?.();
  }

  _clearConnectTimer() {
    if (this.connectTimer) {
      clearTimeout(this.connectTimer);
      this.connectTimer = null;
    }
    if (this._connectTimeoutTimer) {
      clearTimeout(this._connectTimeoutTimer);
      this._connectTimeoutTimer = null;
    }
  }

  _markSeen() {
    this.lastSeenAt = Date.now();
  }

  _startLiveness() {
    this._stopLiveness();
    this._markSeen();
    this.livenessPingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.ping();
        } catch (e) {
          this.logger?.warn?.(`[gateway] ping failed: ${String(e)}`);
        }
      }
    }, LIVENESS_PING_INTERVAL_MS);
    this.livenessPingTimer.unref?.();

    this.livenessCheckTimer = setInterval(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const staleMs = Date.now() - this.lastSeenAt;
      if (staleMs > LIVENESS_TIMEOUT_MS) {
        this.logger?.warn?.(`[gateway] liveness timeout stale_ms=${staleMs}, forcing reconnect`);
        this._stopLiveness();
        try { this.ws.terminate(); } catch {}
      }
    }, LIVENESS_CHECK_INTERVAL_MS);
    this.livenessCheckTimer.unref?.();
  }

  _stopLiveness() {
    if (this.livenessPingTimer) { clearInterval(this.livenessPingTimer); this.livenessPingTimer = null; }
    if (this.livenessCheckTimer) { clearInterval(this.livenessCheckTimer); this.livenessCheckTimer = null; }
  }

  _scheduleReconnect() {
    if (this.closing) return;
    if (this.retry.maxAttempts > 0 && this.attempts >= this.retry.maxAttempts) {
      this.logger?.error?.('[gateway] retry limit reached, giving up');
      return;
    }
    const delay = Math.min(this.backoffMs, this.retry.maxMs);
    this.attempts++;
    this.backoffMs = Math.min(this.backoffMs * 2, this.retry.maxMs);
    this.logger?.info?.(`[gateway] reconnecting in ${delay}ms (attempt ${this.attempts})`);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
    this.reconnectTimer.unref?.();
  }
}
