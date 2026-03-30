import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { GatewayClient } from './gateway-client.js';
import { GatewayBridge } from './gateway-bridge.js';
import { ManusClawHttpServer } from './http-server.js';
import { ManusFileResolver } from './manus-file-resolver.js';

// ─── manus_upload_file tool definition ───────────────────────────────────────

const MANUS_UPLOAD_TOOL_NAME = 'manus_upload_file';

const MANUS_UPLOAD_TOOL_DESCRIPTION =
  'Upload local files from the workspace to the Manus platform so the user can download them. ' +
  'Use this whenever you create or modify a file that the user needs (code, documents, reports, data, etc.). ' +
  'A successful call means the files are already delivered to the user as downloadable file cards — ' +
  'do NOT include any download links, sandbox:// URLs, or markdown hyperlinks to the file in your text response. ' +
  'Simply confirm the file has been sent. ' +
  'Parameters must be local filesystem paths only (absolute, or relative to the workspace directory).';

const MANUS_UPLOAD_TOOL_SCHEMA = {
  type: 'object',
  required: ['paths'],
  additionalProperties: false,
  properties: {
    paths: {
      type: 'array',
      minItems: 1,
      maxItems: 5,
      description: 'Local filesystem paths of files to upload (absolute or workspace-relative).',
      items: { type: 'string', minLength: 1 },
    },
  },
};

const UPLOAD_TIMEOUT_MS = 120_000;
const UPLOAD_META_TTL_MS = 10 * 24 * 60 * 60 * 1000; // 10 days

function _inferMimeType(ext) {
  const map = {
    '.txt': 'text/plain', '.md': 'text/markdown', '.json': 'application/json',
    '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
    '.ts': 'text/x.typescript', '.py': 'text/x-python', '.sh': 'application/x-sh',
    '.csv': 'text/csv', '.xml': 'application/xml', '.yaml': 'application/yaml',
    '.yml': 'application/yaml', '.pdf': 'application/pdf',
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml',
    '.zip': 'application/zip',
  };
  return map[ext] || 'application/octet-stream';
}

/**
 * Validate local files before upload (mirrors kimi-claw's validateKimiUploadLocalFiles).
 * Returns { valid: FileEntry[], errors: string[] }.
 */
async function validateLocalFiles(rawPaths, workspaceDir) {
  const valid = [];
  const errors = [];

  const checks = rawPaths.map(async (rawPath) => {
    const filePath = path.isAbsolute(rawPath) ? rawPath : path.join(workspaceDir, rawPath);
    const fileName = path.basename(filePath);
    try {
      await fsp.access(filePath, fs.constants.R_OK);
      const stat = await fsp.stat(filePath);
      if (!stat.isFile()) {
        errors.push(`${rawPath}: must be a regular file (not a directory)`);
        return;
      }
      valid.push({ filePath, fileName, size: stat.size });
    } catch (err) {
      if (err.code === 'ENOENT') errors.push(`${rawPath}: must exist`);
      else if (err.code === 'EACCES') errors.push(`${rawPath}: must be readable`);
      else errors.push(`${rawPath}: ${err.message}`);
    }
  });
  await Promise.all(checks);
  return { valid, errors };
}

/**
 * Upload a single file with timeout control (mirrors kimi-claw's AbortController pattern).
 */
async function uploadFileToManus({ filePath, fileName, manusApiBaseUrl, manusApiKey }) {
  const fileData = await fsp.readFile(filePath);
  const ext = path.extname(fileName).toLowerCase();
  const mimeType = _inferMimeType(ext);

  const formData = new FormData();
  formData.append('file', new Blob([fileData], { type: mimeType }), fileName);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS);

  try {
    const uploadUrl = `${manusApiBaseUrl}/api/v1/claw/upload`;
    const response = await fetch(uploadUrl, {
      method: 'POST',
      headers: { 'X-Claw-Api-Key': manusApiKey },
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => response.statusText);
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const json = await response.json();
    const data = json?.data;
    if (!data?.file_id) {
      throw new Error(`Unexpected upload response: ${JSON.stringify(json)}`);
    }

    return {
      file_id: data.file_id,
      filename: data.filename || fileName,
      content_type: data.content_type || mimeType,
      size: data.size || fileData.length,
      upload_date: data.upload_date || new Date().toISOString(),
      file_url: data.file_url || null,
    };
  } finally {
    clearTimeout(timer);
  }
}

// ─── Upload metadata cache ─────────────────────────────────────────────────

const UPLOAD_META_DIR_NAME = 'upload_meta';

function getUploadMetaDir(openclawHome) {
  return path.join(openclawHome || '/home/node/.openclaw', 'plugins', 'manus-claw', UPLOAD_META_DIR_NAME);
}

function saveUploadMeta(metaDir, toolCallId, fileId, meta) {
  try {
    fs.mkdirSync(metaDir, { recursive: true });
    if (toolCallId) {
      fs.writeFileSync(path.join(metaDir, `${toolCallId}.json`), JSON.stringify(meta, null, 2));
    }
    if (fileId) {
      fs.writeFileSync(path.join(metaDir, `${fileId}.json`), JSON.stringify(meta, null, 2));
    }
  } catch {}
}

function loadUploadMetaByFileId(metaDir, fileId) {
  try {
    const p = path.join(metaDir, `${fileId}.json`);
    if (fs.existsSync(p)) {
      const meta = JSON.parse(fs.readFileSync(p, 'utf-8'));
      if (meta.timestamp && Date.now() - meta.timestamp < UPLOAD_META_TTL_MS) {
        return meta;
      }
    }
  } catch {}
  return null;
}

function cleanUploadMetaCache(metaDir) {
  try {
    if (!fs.existsSync(metaDir)) return;
    for (const file of fs.readdirSync(metaDir)) {
      const p = path.join(metaDir, file);
      try {
        const meta = JSON.parse(fs.readFileSync(p, 'utf-8'));
        if (meta.timestamp && Date.now() - meta.timestamp > UPLOAD_META_TTL_MS) {
          fs.unlinkSync(p);
        }
      } catch { /* skip non-json */ }
    }
  } catch {}
}

// ─── Plugin config resolution ─────────────────────────────────────────────────

function resolveConfig(pluginConfig, openclawConfig) {
  const cfg = {
    gateway: { url: 'ws://127.0.0.1:18789', token: '', agentId: 'main' },
    server: { port: 18788, host: '0.0.0.0' },
    retry: { baseMs: 1000, maxMs: 60000, maxAttempts: 0 },
    log: { enabled: true, verbose: false },
  };

  const pc = pluginConfig || {};
  const ocGateway = openclawConfig?.gateway || {};

  if (pc.gateway?.url) cfg.gateway.url = pc.gateway.url;
  else if (ocGateway.port) cfg.gateway.url = `ws://127.0.0.1:${ocGateway.port}`;

  if (pc.gateway?.token) cfg.gateway.token = pc.gateway.token;
  else if (ocGateway.auth?.token) cfg.gateway.token = ocGateway.auth.token;

  if (pc.gateway?.agentId) cfg.gateway.agentId = pc.gateway.agentId;
  if (pc.server?.port) cfg.server.port = pc.server.port;
  if (pc.server?.host) cfg.server.host = pc.server.host;
  if (pc.retry?.baseMs) cfg.retry.baseMs = pc.retry.baseMs;
  if (pc.retry?.maxMs) cfg.retry.maxMs = pc.retry.maxMs;
  if (pc.retry?.maxAttempts !== undefined) cfg.retry.maxAttempts = pc.retry.maxAttempts;
  if (pc.log?.enabled !== undefined) cfg.log.enabled = pc.log.enabled;
  if (pc.log?.verbose !== undefined) cfg.log.verbose = pc.log.verbose;

  return cfg;
}

// ─── Plugin definition ────────────────────────────────────────────────────────

const plugin = {
  id: 'manus-claw',
  name: 'manus-claw',
  description: 'Connector plugin that bridges manus backend with the local OpenClaw Gateway.',

  register(context) {
    let gatewayClient = null;
    let gatewayBridge = null;
    let httpServer = null;

    // Manus backend connection info (available as env vars in the container)
    const manusApiBaseUrl = process.env.MANUS_API_BASE_URL || 'http://backend:8000';
    const manusApiKey = process.env.MANUS_API_KEY || '';

    // ── Register manus_upload_file as a native OpenClaw plugin tool ────────────
    // OpenClaw will expose this tool to the LLM automatically. When the agent
    // calls it, OpenClaw invokes execute() below in the plugin's process context.
    const openclawHome = process.env.OPENCLAW_HOME || '/home/node/.openclaw';
    const uploadMetaDir = getUploadMetaDir(openclawHome);

    // Periodically clean expired cache entries
    const cleanInterval = setInterval(() => cleanUploadMetaCache(uploadMetaDir), 3600_000);
    cleanInterval.unref?.();

    context.registerTool({
      name: MANUS_UPLOAD_TOOL_NAME,
      description: MANUS_UPLOAD_TOOL_DESCRIPTION,
      parameters: MANUS_UPLOAD_TOOL_SCHEMA,

      async execute(toolCallId, args) {
        const logger = context.logger;
        const rawPaths = args?.paths || [];
        logger?.info?.(`[manus_upload_file] called toolCallId=${toolCallId} paths=${JSON.stringify(rawPaths)}`);

        const openclawConfig = context.runtime?.config?.loadConfig?.();
        const workspaceDir = openclawConfig?.agents?.defaults?.workspace || '/home/node/.openclaw/workspace';

        // 1) Validate files before uploading (exist, readable, regular file)
        const { valid: validFiles, errors: validationErrors } = await validateLocalFiles(rawPaths, workspaceDir);

        if (validationErrors.length > 0 && validFiles.length === 0) {
          const errText = validationErrors.join('\n');
          return {
            output: { ok: false, error: errText },
            result: { ok: false, error: errText },
            content: [{ type: 'text', text: `File validation failed:\n${errText}` }],
            isError: true,
          };
        }

        // 2) Upload each valid file with timeout
        const uploaded = [];
        const uploadErrors = [...validationErrors];

        for (const { filePath, fileName, size } of validFiles) {
          try {
            const fileInfo = await uploadFileToManus({ filePath, fileName, manusApiBaseUrl, manusApiKey });
            uploaded.push(fileInfo);
            logger?.info?.(`[manus_upload_file] uploaded ${fileName} -> file_id=${fileInfo.file_id}`);

            // 3) Notify via gateway bridge so frontend receives the file card
            gatewayBridge?.notifyFileUploaded(fileInfo);

            // 4) Cache upload metadata (per fileId + per toolCallId)
            const meta = { ...fileInfo, toolCallId, timestamp: Date.now(), localPath: filePath };
            saveUploadMeta(uploadMetaDir, null, fileInfo.file_id, meta);
          } catch (err) {
            const msg = err.name === 'AbortError' ? `upload timed out after ${UPLOAD_TIMEOUT_MS / 1000}s` : String(err);
            uploadErrors.push(`${fileName}: ${msg}`);
            logger?.warn?.(`[manus_upload_file] upload failed for ${fileName}: ${msg}`);
          }
        }

        if (uploaded.length === 0) {
          const errText = uploadErrors.join('\n');
          return {
            output: { ok: false, error: errText },
            result: { ok: false, error: errText },
            content: [{ type: 'text', text: `Upload failed:\n${errText}` }],
            isError: true,
          };
        }

        // 5) Save per-toolCallId cache for the entire batch
        const batchMeta = { toolCallId, files: uploaded, timestamp: Date.now() };
        saveUploadMeta(uploadMetaDir, toolCallId, null, batchMeta);

        // 6) Return resource_link content blocks with manus-file:// URIs
        const content = uploaded.map(u => ({
          type: 'resource_link',
          uri: `manus-file://${u.file_id}`,
          name: u.filename,
          mimeType: u.content_type,
        }));

        const filesResult = uploaded.map(u => ({
          name: u.filename,
          file_id: u.file_id,
          uri: `manus-file://${u.file_id}`,
        }));
        const result = { ok: true, files: filesResult };

        if (uploadErrors.length > 0) {
          content.push({ type: 'text', text: `Partial failures:\n${uploadErrors.join('\n')}` });
        }

        logger?.info?.(`[manus_upload_file] result=${JSON.stringify(result)}`);
        return { output: result, result, content, isError: false };
      },
    });

    // ── Register the main service ──────────────────────────────────────────────
    context.registerService({
      id: 'manus-claw',

      start: (runtime) => {
        const openclawConfig = runtime?.config?.loadConfig?.();
        const cfg = resolveConfig(context.pluginConfig ?? {}, openclawConfig);
        const workspaceDir = openclawConfig?.agents?.defaults?.workspace || '/home/node/.openclaw/workspace';

        const logger = context.logger;

        if (cfg.log.enabled) {
          logger?.info?.(`[manus-claw] starting with gateway=${cfg.gateway.url} server=${cfg.server.host}:${cfg.server.port}`);
        }

        gatewayBridge = new GatewayBridge({ agentId: cfg.gateway.agentId, logger });

        gatewayClient = new GatewayClient({
          url: cfg.gateway.url,
          token: cfg.gateway.token,
          agentId: cfg.gateway.agentId,
          logger,
          retry: cfg.retry,
          onReady: async () => { await gatewayBridge.onGatewayReady(); },
          onMessage: (msg) => { gatewayBridge.handleGatewayMessage(msg); },
          onClose: () => { gatewayBridge.handleGatewayDisconnected(); },
        });

        gatewayBridge.gatewayClient = gatewayClient;

        // File resolver: manus-file:// → download → <MANUS_FILE />
        const fileDownloadDir = path.join(workspaceDir, 'download');
        const fileResolver = new ManusFileResolver({
          manusApiBaseUrl,
          manusApiKey,
          downloadDir: fileDownloadDir,
          uploadMetaDir,
          logger,
        });
        gatewayBridge.fileResolver = fileResolver;

        httpServer = new ManusClawHttpServer({
          port: cfg.server.port,
          host: cfg.server.host,
          logger,
          gatewayBridge,
          workspaceDir,
          openclawHome: process.env.OPENCLAW_HOME || '/home/node/.openclaw',
          agentId: cfg.gateway.agentId,
        });

        gatewayClient.start();
        httpServer.start();
      },

      stop: () => {
        gatewayClient?.stop();
        httpServer?.stop();
        gatewayClient = null;
        gatewayBridge = null;
        httpServer = null;
      },
    });
  },
};

export default plugin;
