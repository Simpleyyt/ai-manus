#!/usr/bin/env node
/**
 * Resolve manus.im session_id JWT from env / file.
 * Default: print JSON metadata only (no token).
 *   --token   print raw JWT to stdout (for piping into inject; never log)
 *   --check   exit 0 if resolvable, 1 otherwise
 *
 * Sources (first wins):
 *   1. MANUS_SESSION_TOKEN  — raw JWT
 *   2. MANUS_COOKIE         — full Cookie header or "session_id=..."
 *   3. MANUS_SESSION_FILE   — path to file (default /tmp/manus_session_id.value)
 */
const fs = require('fs')

function extractFromCookieHeader(raw) {
  const s = String(raw || '').trim()
  if (!s) return ''
  if (!s.includes('=') && !s.includes(';')) return s // bare JWT
  for (const part of s.split(';')) {
    const [k, ...rest] = part.trim().split('=')
    if (k && k.trim().toLowerCase() === 'session_id') {
      return rest.join('=').trim()
    }
  }
  return ''
}

function looksJwt(v) {
  return typeof v === 'string' && v.length > 40 && (v.match(/\./g) || []).length >= 2
}

function resolve() {
  const fromToken = String(process.env.MANUS_SESSION_TOKEN || '').trim()
  if (looksJwt(fromToken)) {
    return { source: 'MANUS_SESSION_TOKEN', value: fromToken }
  }

  const fromCookie = extractFromCookieHeader(process.env.MANUS_COOKIE || '')
  if (looksJwt(fromCookie)) {
    return { source: 'MANUS_COOKIE', value: fromCookie }
  }

  const filePath =
    process.env.MANUS_SESSION_FILE || '/tmp/manus_session_id.value'
  if (fs.existsSync(filePath)) {
    const fromFile = extractFromCookieHeader(fs.readFileSync(filePath, 'utf8'))
    if (looksJwt(fromFile)) {
      return { source: `file:${filePath}`, value: fromFile }
    }
  }

  return null
}

const mode = process.argv.includes('--token')
  ? 'token'
  : process.argv.includes('--check')
    ? 'check'
    : 'meta'

const hit = resolve()
if (!hit) {
  const meta = {
    ok: false,
    sourcesTried: [
      'MANUS_SESSION_TOKEN',
      'MANUS_COOKIE',
      process.env.MANUS_SESSION_FILE || '/tmp/manus_session_id.value',
    ],
  }
  if (mode === 'token') {
    process.stderr.write('manus-official-cdp: no session_id in env/file\n')
    process.exit(1)
  }
  process.stdout.write(JSON.stringify(meta) + '\n')
  process.exit(mode === 'check' ? 1 : 0)
}

const meta = {
  ok: true,
  source: hit.source,
  valueLen: hit.value.length,
  valuePrefix: hit.value.slice(0, 12),
  jwtish: looksJwt(hit.value),
}

if (mode === 'token') {
  process.stdout.write(hit.value)
  process.exit(0)
}

process.stdout.write(JSON.stringify(meta) + '\n')
process.exit(0)
