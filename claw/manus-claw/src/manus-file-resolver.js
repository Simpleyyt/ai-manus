import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';

const MANUS_FILE_URI_PREFIX = 'manus-file://';
const MANUS_FILE_URI_REGEX = /manus-file:\/\/([a-f0-9]{24})/g;
const RESOLVE_TIMEOUT_MS = 30_000;
const MAX_FILENAME_LENGTH = 120;

/**
 * Resolves `manus-file://{fileId}` URIs found in prompts by:
 *   1. Downloading the file from the Manus backend API to local disk
 *   2. Replacing the URI with a `<MANUS_FILE .../>` tag the agent can use
 *
 * Mirrors kimi-claw's KimiFileResolver pattern:
 *   - Local download cache at `{downloadDir}/{fileId}_{sanitizedName}`
 *   - Metadata fetch + signed-URL download
 *   - Timeout control via AbortController
 *   - Graceful degradation on failure (tag with status="download_failed")
 */
export class ManusFileResolver {
  constructor({ manusApiBaseUrl, manusApiKey, downloadDir, uploadMetaDir, logger }) {
    this.manusApiBaseUrl = manusApiBaseUrl;
    this.manusApiKey = manusApiKey;
    this.downloadDir = downloadDir;
    this.uploadMetaDir = uploadMetaDir;
    this.logger = logger;

    try { fs.mkdirSync(this.downloadDir, { recursive: true }); } catch {}
  }

  /**
   * Scan text for manus-file:// URIs and return unique fileIds.
   */
  buildResolutionPlan(text) {
    const fileIds = new Set();
    let match;
    const re = new RegExp(MANUS_FILE_URI_REGEX.source, 'g');
    while ((match = re.exec(text)) !== null) {
      fileIds.add(match[1]);
    }
    return [...fileIds];
  }

  /**
   * Full pipeline: detect → resolve → replace all manus-file:// URIs in text.
   * Returns the transformed text with <MANUS_FILE .../> tags.
   */
  async resolvePrompt(text) {
    if (typeof text !== 'string') return text;

    const fileIds = this.buildResolutionPlan(text);
    if (fileIds.length === 0) return text;

    this.logger?.info?.(`[file-resolver] found ${fileIds.length} manus-file:// refs to resolve`);

    const resolutions = new Map();
    await Promise.all(fileIds.map(async (fileId) => {
      const result = await this._resolveFile(fileId);
      resolutions.set(fileId, result);
    }));

    let resolved = text;
    for (const [fileId, result] of resolutions) {
      const uriPattern = new RegExp(`manus-file://${fileId}`, 'g');
      const tag = result.ok
        ? buildManusFileRefText(result)
        : buildManusFileFailedRefText(result);
      resolved = resolved.replace(uriPattern, tag);
    }

    return resolved;
  }

  /**
   * Resolve a single fileId:
   *   1. Check local download cache
   *   2. Check upload_meta cache for local path
   *   3. Fetch file metadata from backend
   *   4. Download file content to local cache
   */
  async _resolveFile(fileId) {
    // 1. Check local download cache (files named {fileId}_{name})
    const cached = this._findExistingDownload(fileId);
    if (cached) {
      this.logger?.info?.(`[file-resolver] cache hit for ${fileId}: ${cached.localPath}`);
      return { ok: true, fileId, localPath: cached.localPath, name: cached.name };
    }

    // 2. Check upload_meta for a local path from a recent upload
    const uploadMeta = this._loadUploadMeta(fileId);
    if (uploadMeta?.localPath) {
      try {
        const stat = await fsp.stat(uploadMeta.localPath);
        if (stat.isFile() && stat.size > 0) {
          this.logger?.info?.(`[file-resolver] upload-meta hit for ${fileId}: ${uploadMeta.localPath}`);
          return {
            ok: true, fileId,
            localPath: uploadMeta.localPath,
            name: uploadMeta.filename || path.basename(uploadMeta.localPath),
          };
        }
      } catch {}
    }

    // 3. Fetch metadata from backend
    let meta;
    try {
      meta = await this._fetchFileMeta(fileId);
    } catch (err) {
      const reason = err.name === 'AbortError' ? 'timeout' : `meta_fetch_failed: ${err.message}`;
      this.logger?.warn?.(`[file-resolver] metadata fetch failed for ${fileId}: ${reason}`);
      return { ok: false, fileId, name: fileId, reason };
    }

    // 4. Download file content
    try {
      const localPath = await this._downloadFile(fileId, meta);
      this.logger?.info?.(`[file-resolver] downloaded ${fileId} -> ${localPath}`);
      return { ok: true, fileId, localPath, name: meta.filename || fileId };
    } catch (err) {
      const reason = err.name === 'AbortError' ? 'timeout' : `download_failed: ${err.message}`;
      this.logger?.warn?.(`[file-resolver] download failed for ${fileId}: ${reason}`);
      return { ok: false, fileId, name: meta.filename || fileId, reason };
    }
  }

  /**
   * Find a previously downloaded file by fileId prefix in downloadDir.
   * Mirrors kimi-claw's findExistingKimiFileDownload.
   */
  _findExistingDownload(fileId) {
    try {
      if (!fs.existsSync(this.downloadDir)) return null;
      const prefix = `${fileId}_`;
      const entries = fs.readdirSync(this.downloadDir, { withFileTypes: true });
      for (const entry of entries) {
        if (!entry.isFile() || !entry.name.startsWith(prefix)) continue;
        const filePath = path.join(this.downloadDir, entry.name);
        const stat = fs.statSync(filePath);
        if (stat.isFile() && stat.size > 0) {
          const name = entry.name.slice(prefix.length) || 'file';
          return { localPath: filePath, name };
        }
      }
    } catch {}
    return null;
  }

  /**
   * Load upload metadata from the upload_meta cache.
   */
  _loadUploadMeta(fileId) {
    if (!this.uploadMetaDir) return null;
    try {
      const metaPath = path.join(this.uploadMetaDir, `${fileId}.json`);
      if (!fs.existsSync(metaPath)) return null;
      return JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
    } catch {}
    return null;
  }

  /**
   * Fetch file metadata from the Manus backend.
   * GET /api/v1/claw/resolve/{fileId} with X-Claw-Api-Key header.
   */
  async _fetchFileMeta(fileId) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), RESOLVE_TIMEOUT_MS);

    try {
      const url = `${this.manusApiBaseUrl}/api/v1/claw/resolve/${encodeURIComponent(fileId)}`;
      const resp = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Claw-Api-Key': this.manusApiKey || '',
          'Accept': 'application/json',
        },
        signal: controller.signal,
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const json = await resp.json();
      const data = json?.data || json;
      return {
        fileId,
        filename: data.filename || data.name || fileId,
        contentType: data.content_type || data.contentType || 'application/octet-stream',
        size: data.size || 0,
      };
    } finally {
      clearTimeout(timer);
    }
  }

  /**
   * Download file content to local cache directory.
   * GET /api/v1/claw/resolve/{fileId}/download with X-Claw-Api-Key header.
   * File is saved as {fileId}_{sanitizedFilename}.
   */
  async _downloadFile(fileId, meta) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), RESOLVE_TIMEOUT_MS);

    try {
      const downloadUrl = `${this.manusApiBaseUrl}/api/v1/claw/resolve/${encodeURIComponent(fileId)}/download`;
      const resp = await fetch(downloadUrl, {
        method: 'GET',
        headers: { 'X-Claw-Api-Key': this.manusApiKey || '' },
        signal: controller.signal,
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const buffer = Buffer.from(await resp.arrayBuffer());
      const safeName = sanitizeFileName(meta.filename || 'file');
      const destPath = path.join(this.downloadDir, `${fileId}_${safeName}`);

      await fsp.writeFile(destPath, buffer);
      return destPath;
    } finally {
      clearTimeout(timer);
    }
  }
}

// ─── Tag builders ─────────────────────────────────────────────────────────────

function escapeXmlAttribute(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function buildManusFileRefText({ fileId, localPath, name }) {
  return `<MANUS_FILE type="file" path="${escapeXmlAttribute(localPath)}" name="${escapeXmlAttribute(name)}" id="${escapeXmlAttribute(fileId)}" />`;
}

function buildManusFileFailedRefText({ fileId, name, reason }) {
  return `<MANUS_FILE type="file" path="" name="${escapeXmlAttribute(name)}" id="${escapeXmlAttribute(fileId)}" status="download_failed" reason="${escapeXmlAttribute(reason)}" />`;
}

/**
 * Sanitize filename for local storage.
 * Strips path separators, control chars, replaces unsafe chars with _,
 * truncates to MAX_FILENAME_LENGTH.
 */
function sanitizeFileName(name) {
  let safe = path.basename(name);
  safe = safe.replace(/[\x00-\x1f\x7f]/g, '');
  safe = safe.replace(/[/\\:*?"<>|]/g, '_');
  safe = safe.replace(/_+/g, '_');
  if (safe.length > MAX_FILENAME_LENGTH) {
    const ext = path.extname(safe);
    safe = safe.slice(0, MAX_FILENAME_LENGTH - ext.length) + ext;
  }
  return safe || 'file';
}
