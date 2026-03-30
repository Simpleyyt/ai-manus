import fs from 'node:fs';
import path from 'node:path';

const LOCAL_HISTORY_LIMIT = 200;
const TAIL_MAX_BYTES = 1_048_576; // 1 MB

/**
 * Reads OpenClaw's native session history from .jsonl files.
 * Mirrors kimi-claw's AcpGatewayLocalSessionHistory approach:
 *   read from tail of .jsonl → parse → filter → reverse to chronological order.
 */
export class SessionHistory {
  constructor({ openclawHome, agentId, logger }) {
    this.openclawHome = openclawHome || '/home/node/.openclaw';
    this.agentId = agentId || 'main';
    this.logger = logger;
  }

  /**
   * Read the most recent entries from a session's .jsonl file.
   * Returns an array in chronological order (oldest first).
   */
  readEntries(sessionId, limit = LOCAL_HISTORY_LIMIT) {
    const sessionsDir = path.join(this.openclawHome, 'agents', this.agentId, 'sessions');
    const indexPath = path.join(sessionsDir, 'sessions.json');

    let jsonlPath = null;

    // Try to find the session file from the index
    // sessions.json can be:
    //   - An object keyed by sessionKey, each value has { sessionId, sessionFile, ... }
    //   - An array of session entries
    try {
      if (fs.existsSync(indexPath)) {
        const raw = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
        let entries = [];

        if (Array.isArray(raw)) {
          entries = raw;
        } else if (raw && typeof raw === 'object') {
          // Object keyed by sessionKey
          entries = Object.entries(raw).map(([key, val]) => ({
            ...(typeof val === 'object' ? val : {}),
            sessionKey: key,
          }));
        }

        const entry = entries.find(
          s => s.sessionId === sessionId || s.sessionKey === sessionId
              || s.id === sessionId
              // Also match partial sessionKey suffix (e.g. "manus-main" matches "agent:main:manus:main")
              || (s.sessionKey && s.sessionKey.includes(sessionId)),
        );
        if (entry?.sessionFile) {
          jsonlPath = path.isAbsolute(entry.sessionFile)
            ? entry.sessionFile
            : path.join(sessionsDir, entry.sessionFile);
        }
      }
    } catch (err) {
      this.logger?.warn?.(`[session-history] failed to read sessions index: ${err}`);
    }

    if (!jsonlPath) {
      jsonlPath = path.join(sessionsDir, `${sessionId}.jsonl`);
    }

    if (!fs.existsSync(jsonlPath)) {
      this.logger?.info?.(`[session-history] no session file found: ${jsonlPath}`);
      return [];
    }

    return this._readTailEntries(jsonlPath, limit);
  }

  /**
   * List available session IDs.
   */
  listSessions() {
    const sessionsDir = path.join(this.openclawHome, 'agents', this.agentId, 'sessions');
    const indexPath = path.join(sessionsDir, 'sessions.json');

    try {
      if (fs.existsSync(indexPath)) {
        const raw = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
        let entries = [];
        if (Array.isArray(raw)) {
          entries = raw;
        } else if (raw && typeof raw === 'object') {
          entries = Object.entries(raw).map(([key, val]) => ({
            ...(typeof val === 'object' ? val : {}),
            sessionKey: key,
          }));
        }
        return entries.map(s => ({
          sessionId: s.sessionId || s.id,
          sessionKey: s.sessionKey,
          sessionFile: s.sessionFile,
        }));
      }
    } catch {}

    // Fallback: list .jsonl files
    try {
      return fs.readdirSync(sessionsDir)
        .filter(f => f.endsWith('.jsonl'))
        .map(f => ({ sessionId: f.replace('.jsonl', '') }));
    } catch {
      return [];
    }
  }

  _readTailEntries(filePath, limit) {
    const entries = [];
    try {
      const stat = fs.statSync(filePath);
      const readSize = Math.min(stat.size, TAIL_MAX_BYTES);
      const fd = fs.openSync(filePath, 'r');
      const buf = Buffer.alloc(readSize);
      fs.readSync(fd, buf, 0, readSize, stat.size - readSize);
      fs.closeSync(fd);

      const text = buf.toString('utf-8');
      // If we started mid-file, discard the first (possibly partial) line
      const lines = text.split('\n');
      if (readSize < stat.size) lines.shift();

      for (let i = lines.length - 1; i >= 0 && entries.length < limit; i--) {
        const line = lines[i].trim();
        if (!line) continue;

        let parsed;
        try { parsed = JSON.parse(line); } catch { continue; }

        if (!parsed || parsed.type !== 'message' || !parsed.message) continue;
        const msg = parsed.message;
        const role = msg.role;
        if (role !== 'user' && role !== 'assistant' && role !== 'toolResult') continue;

        entries.push({
          role,
          content: msg.content,
          toolCallId: msg.toolCallId || msg.tool_call_id || undefined,
          toolName: msg.toolName || msg.tool_name || undefined,
          stopReason: msg.stopReason || msg.stop_reason || undefined,
          timestamp: parsed.ts || msg.timestamp || undefined,
        });
      }
    } catch (err) {
      this.logger?.warn?.(`[session-history] failed to read ${filePath}: ${err}`);
    }

    entries.reverse();
    return entries;
  }
}
