#!/usr/bin/env node
/**
 * Auto-fetch manus.im session_id and write /tmp/manus_session_id.value (0600).
 *
 * Sources (first wins unless --force-fetch):
 *   1. Existing env/file via resolve-session.cjs (skip with --force-fetch)
 *   2. CDP Chrome on MANUS_CDP_URL (default http://127.0.0.1:9222)
 *   3. Decrypt Chrome Cookies DB (Default + common /tmp CDP profiles)
 *
 * Output (default): JSON metadata only — never prints full JWT.
 *   --token     print raw JWT to stdout
 *   --export    print: export MANUS_SESSION_TOKEN='...'
 *   --force-fetch  ignore existing env/file; re-read CDP/DB
 *   --no-write  do not write the temp file
 *
 * Env:
 *   MANUS_CDP_URL          CDP endpoint (default http://127.0.0.1:9222)
 *   MANUS_SESSION_FILE     output path (default /tmp/manus_session_id.value)
 *   MANUS_CHROME_COOKIES   override Cookies DB path
 *   PLAYWRIGHT_CORE        path to playwright-core package root
 */
const fs = require('fs')
const os = require('os')
const path = require('path')
const crypto = require('crypto')
const { spawnSync } = require('child_process')

const OUT =
  process.env.MANUS_SESSION_FILE || '/tmp/manus_session_id.value'
const CDP_URL = process.env.MANUS_CDP_URL || 'http://127.0.0.1:9222'
const SCRIPT_DIR = __dirname

function looksJwt(v) {
  return typeof v === 'string' && v.length > 40 && (v.match(/\./g) || []).length >= 2
}

function metaOf(source, value) {
  return {
    ok: true,
    source,
    valueLen: value.length,
    valuePrefix: value.slice(0, 12),
    jwtish: looksJwt(value),
    file: OUT,
  }
}

function writeToken(value) {
  fs.writeFileSync(OUT, value, { mode: 0o600 })
  try {
    fs.chmodSync(OUT, 0o600)
  } catch {
    /* ignore */
  }
}

function tryResolveExisting() {
  try {
    const r = spawnSync(
      process.execPath,
      [path.join(SCRIPT_DIR, 'resolve-session.cjs'), '--token'],
      { encoding: 'utf8' },
    )
    if (r.status === 0 && looksJwt(r.stdout.trim())) {
      return { source: 'resolve-session', value: r.stdout.trim() }
    }
  } catch {
    /* ignore */
  }
  return null
}

function findPlaywrightCore() {
  const candidates = [
    process.env.PLAYWRIGHT_CORE,
    '/tmp/pw/node_modules/playwright-core',
    path.join(process.cwd(), 'tmp/pw/node_modules/playwright-core'),
    path.join(process.cwd(), 'node_modules/playwright-core'),
  ].filter(Boolean)
  for (const c of candidates) {
    try {
      if (fs.existsSync(path.join(c, 'package.json'))) return c
    } catch {
      /* ignore */
    }
  }
  return null
}

async function tryCdp() {
  let version
  try {
    const res = await fetch(`${CDP_URL.replace(/\/$/, '')}/json/version`, {
      signal: AbortSignal.timeout(2000),
    })
    if (!res.ok) return null
    version = await res.json()
  } catch {
    return null
  }

  const pwRoot = findPlaywrightCore()
  if (!pwRoot) {
    return {
      error: 'cdp_up_but_no_playwright',
      cdp: CDP_URL,
      browser: version.Browser,
    }
  }

  const { chromium } = require(pwRoot)
  const browser = await chromium.connectOverCDP(CDP_URL)
  try {
    const context = browser.contexts()[0]
    if (!context) return null
    const cookies = await context.cookies(['https://manus.im', 'https://www.manus.im'])
    const session = cookies.find((c) => c.name === 'session_id')
    if (session && looksJwt(session.value)) {
      return { source: `cdp:${CDP_URL}`, value: session.value }
    }
    return { error: 'cdp_no_session_id', cdp: CDP_URL }
  } finally {
    await browser.close().catch(() => {})
  }
}

function chromeSafeStoragePassword() {
  const r = spawnSync(
    'security',
    ['find-generic-password', '-w', '-s', 'Chrome Safe Storage', '-a', 'Chrome'],
    { encoding: 'utf8' },
  )
  if (r.status !== 0) {
    throw new Error(
      (r.stderr || r.stdout || 'keychain read failed').trim() ||
        'Chrome Safe Storage keychain denied',
    )
  }
  return r.stdout.trim()
}

function decryptChromeValue(enc, password) {
  if (!enc || enc.length < 4) return ''
  const prefix = enc.subarray(0, 3).toString('utf8')
  if (prefix !== 'v10' && prefix !== 'v11') {
    // plaintext (rare) or unsupported scheme (e.g. v20 app-bound)
    if (enc[0] === 0x76 /* v */) return ''
    return enc.toString('utf8')
  }
  const key = crypto.pbkdf2Sync(password, 'saltysalt', 1003, 16, 'sha1')
  const iv = Buffer.alloc(16, ' ')
  const decipher = crypto.createDecipheriv('aes-128-cbc', key, iv)
  let dec = Buffer.concat([decipher.update(enc.subarray(3)), decipher.final()])
  const pad = dec[dec.length - 1]
  if (pad >= 1 && pad <= 16) dec = dec.subarray(0, dec.length - pad)
  let text = dec.toString('utf8')
  if (!looksJwt(text) && dec.length > 32) {
    const alt = dec.subarray(32).toString('utf8')
    if (looksJwt(alt)) text = alt
  }
  return text
}

function cookieDbCandidates() {
  const home = os.homedir()
  const list = []
  if (process.env.MANUS_CHROME_COOKIES) list.push(process.env.MANUS_CHROME_COOKIES)
  list.push(
    path.join(home, 'Library/Application Support/Google/Chrome/Default/Cookies'),
    path.join(home, 'Library/Application Support/Google/Chrome/Default/Network/Cookies'),
    path.join(home, 'Library/Application Support/Google/Chrome/Profile 1/Cookies'),
    '/tmp/chrome-yaoyitao-local/Default/Cookies',
    '/tmp/chrome-manus-cdp/Default/Cookies',
    '/tmp/chrome-manus-debug/Default/Cookies',
  )
  return list.filter((p, i, a) => a.indexOf(p) === i && fs.existsSync(p))
}

function tryChromeDb() {
  let password
  try {
    password = chromeSafeStoragePassword()
  } catch (e) {
    return { error: 'keychain', message: String(e.message || e) }
  }

  const dbs = cookieDbCandidates()
  if (!dbs.length) return { error: 'no_cookie_db' }

  let lastError
  for (const dbPath of dbs) {
    const tmp = path.join(
      os.tmpdir(),
      `manus-cookies-${process.pid}-${Date.now()}.db`,
    )
    try {
      fs.copyFileSync(dbPath, tmp)
      try {
        fs.copyFileSync(dbPath + '-journal', tmp + '-journal')
      } catch {
        /* optional */
      }

      let row
      try {
        row = querySessionRow(tmp)
      } finally {
        try {
          fs.unlinkSync(tmp)
        } catch {
          /* ignore */
        }
        try {
          fs.unlinkSync(tmp + '-journal')
        } catch {
          /* ignore */
        }
      }
      if (!row) continue

      let value = row.value || ''
      if ((!value || !looksJwt(value)) && row.encrypted_value) {
        value = decryptChromeValue(row.encrypted_value, password)
      }
      if (looksJwt(value)) {
        return { source: `chrome-db:${dbPath}`, value }
      }
    } catch (e) {
      lastError = String(e.message || e)
    }
  }
  return {
    error: 'chrome_db_no_session',
    dbsTried: dbs,
    lastDbError: lastError,
  }
}

function querySessionRow(dbPath) {
  // Try better-sqlite3
  try {
    const Database = require('better-sqlite3')
    const db = new Database(dbPath, { readonly: true, fileMustExist: true })
    try {
      const row = db
        .prepare(
          `SELECT host_key, value, encrypted_value FROM cookies
           WHERE name = 'session_id' AND host_key LIKE '%manus%'
           ORDER BY LENGTH(encrypted_value) + LENGTH(value) DESC LIMIT 1`,
        )
        .get()
      if (!row) return null
      return {
        value: row.value || '',
        encrypted_value: row.encrypted_value
          ? Buffer.from(row.encrypted_value)
          : null,
      }
    } finally {
      db.close()
    }
  } catch {
    /* fall through to sqlite3 CLI */
  }

  const sql =
    `SELECT quote(value), hex(encrypted_value) FROM cookies ` +
    `WHERE name='session_id' AND host_key LIKE '%manus%' ` +
    `ORDER BY length(encrypted_value)+length(value) DESC LIMIT 1;`
  const r = spawnSync('sqlite3', [dbPath, sql], { encoding: 'utf8' })
  if (r.status !== 0) {
    throw new Error((r.stderr || 'sqlite3 failed').trim())
  }
  const line = (r.stdout || '').trim()
  if (!line) return null
  // quote(value)|hex
  const pipe = line.lastIndexOf('|')
  let value = ''
  let hex = line
  if (pipe >= 0) {
    value = line.slice(0, pipe)
    hex = line.slice(pipe + 1)
    // sqlite quote() wraps in single quotes and escapes ''
    if (value.startsWith("'") && value.endsWith("'")) {
      value = value.slice(1, -1).replace(/''/g, "'")
    }
  }
  const encrypted_value = hex && /^[0-9A-Fa-f]+$/.test(hex) ? Buffer.from(hex, 'hex') : null
  return { value, encrypted_value }
}

function finish(hit, opts) {
  if (!opts.noWrite) writeToken(hit.value)
  const m = metaOf(hit.source, hit.value)
  m.wrote = !opts.noWrite

  if (opts.mode === 'token') {
    process.stdout.write(hit.value)
    process.exit(0)
  }
  if (opts.mode === 'export') {
    // Single-quoted shell export; escape embedded quotes
    const q = hit.value.replace(/'/g, `'\"'\"'`)
    process.stdout.write(`export MANUS_SESSION_TOKEN='${q}'\n`)
    process.stdout.write(`export MANUS_SESSION_FILE='${OUT}'\n`)
    process.exit(0)
  }
  process.stdout.write(JSON.stringify(m) + '\n')
  process.exit(0)
}

async function main() {
  const args = new Set(process.argv.slice(2))
  const opts = {
    mode: args.has('--token') ? 'token' : args.has('--export') ? 'export' : 'meta',
    forceFetch: args.has('--force-fetch'),
    noWrite: args.has('--no-write'),
  }

  const errors = []

  if (!opts.forceFetch) {
    const existing = tryResolveExisting()
    if (existing) {
      // Refresh file so MANUS_SESSION_FILE stays in sync
      finish(existing, opts)
    }
  }

  try {
    const cdp = await tryCdp()
    if (cdp && cdp.value) finish(cdp, opts)
    if (cdp && cdp.error) errors.push(cdp)
  } catch (e) {
    errors.push({ error: 'cdp_exception', message: String(e.message || e) })
  }

  const db = tryChromeDb()
  if (db && db.value) finish(db, opts)
  if (db && db.error) errors.push(db)

  process.stdout.write(
    JSON.stringify({
      ok: false,
      file: OUT,
      errors,
      hint:
        'Log into manus.im in Chrome, allow Keychain access if prompted, ' +
        'or start CDP Chrome on :9222; or export MANUS_SESSION_TOKEN manually ' +
        '(see manus-official-cdp skill).',
    }) + '\n',
  )
  process.exit(1)
}

main().catch((e) => {
  process.stderr.write(String(e.stack || e) + '\n')
  process.exit(1)
})
