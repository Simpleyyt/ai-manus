---
name: manus-official-cdp
description: >-
  Use when opening logged-in manus.im via Chrome CDP without a fresh login —
  auto-fetch session via fetch-session.cjs (CDP/Chrome DB), or read
  MANUS_SESSION_TOKEN / MANUS_COOKIE, or instruct user how to export/give
  `session_id`; triggers: CDP cookie, session_id, 免登录, 环境变量,
  fetch-session, MANUS_SESSION_TOKEN, inject cookie, Default profile,
  怎么获取 cookie, manus.im unavailable, connectOverCDP.
---

# Manus official CDP session

Get a **logged-in** manus.im tab over Chrome DevTools Protocol using `session_id` from **env**, file, or Chrome Default profile — no interactive login when the JWT is still valid.

Pairs with **replicate-manus-ui** (DOM / className mining). Respond in **中文** unless the user writes in English.

## Hard rules

1. **Only `session_id` is required** for auth (domain `.manus.im`). Skip analytics (`_gcl_au`, `__stripe_*`, Intercom, `_fbp`, `_ga`, theme, ad-consent).
2. **Never commit** cookie values, JWT strings, profile copies, or env files that contain them. Never echo the full token in chat / logs / screenshots captions — print `valueLen` + prefix only.
3. Prefer **reuse an already-open CDP Chrome** (`http://127.0.0.1:9222`) over launching a second profile that fights locks.
4. Auth proof = API **200**, not “page isn’t `/login`”. Geo block can still show `/unavailable`.
5. **Always resolve session before asking the user** — env → file → CDP cookies → only then instruct 获取/交给.
6. If still missing, **do not invent workarounds** — tell the user how to export it and how to send it (incl. env vars), then wait.

## Resolve order (agent MUST follow)

```text
0. fetch-session.cjs                 auto: CDP → Chrome DB → write file
1. MANUS_SESSION_TOKEN               raw JWT
2. MANUS_COOKIE                      Cookie header or session_id=...
3. MANUS_SESSION_FILE                default /tmp/manus_session_id.value
4. CDP context.cookies()             already on .manus.im
5. Ask user (获取 + 交给 agent)
```

### Auto-fetch script（推荐）

从本机 **已登录** 的 CDP Chrome 或 Chrome Default Cookies 自动取出 `session_id`，写入 `/tmp/manus_session_id.value`（`0600`），**默认不打印完整 JWT**：

```bash
node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs
# {"ok":true,"source":"cdp:http://127.0.0.1:9222","valueLen":341,...}

eval "$(node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs --export)"
node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs --force-fetch
TOKEN="$(node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs --token)"
```

依赖：CDP `:9222` + `playwright-core`（`/tmp/pw` 或 `PLAYWRIGHT_CORE`）；否则解密 Chrome Cookies（Keychain「Chrome Safe Storage」+ `sqlite3`，可能弹授权）。

Agent 开干前先跑 `fetch-session.cjs`；`ok:false` 再教用户手动获取。

只读已有 env/file（不抓取）：

```bash
node .cursor/skills/manus-official-cdp/scripts/resolve-session.cjs
TOKEN="$(node .cursor/skills/manus-official-cdp/scripts/resolve-session.cjs --token)"
```

In Node/Playwright scripts, read the same sources yourself if the helper is unavailable:

```js
function resolveManusSession() {
  const bare = (process.env.MANUS_SESSION_TOKEN || '').trim()
  if (bare.includes('.')) return bare
  const cookie = process.env.MANUS_COOKIE || ''
  const m = cookie.match(/(?:^|;\s*)session_id=([^;]+)/i)
  if (m) return m[1].trim()
  const file = process.env.MANUS_SESSION_FILE || '/tmp/manus_session_id.value'
  try {
    const t = require('fs').readFileSync(file, 'utf8').trim()
    const m2 = t.match(/(?:^|;\s*)session_id=([^;]+)/i)
    return (m2 ? m2[1] : t).trim()
  } catch { return '' }
}
```

## Tell the user: how to get + how to give

When the agent needs a cookie from the human, paste instructions in **中文** (unless they write in English). Keep it short; do not ask for analytics cookies.

### How to get（获取）

Ask them to use a browser where they are **already logged into** [manus.im](https://manus.im/app):

**方式 A — DevTools（推荐）**

1. 打开已登录的 `https://manus.im/app`
2. `F12` / 右键检查 → **Application**（应用）→ **Cookies** → `https://manus.im`
3. 找到名为 **`session_id`** 的那一行（domain 多为 `.manus.im`）
4. 双击 **Value**，全选复制（一长串 `eyJ…` JWT）

**方式 B — 任意请求的 Cookie 头**

1. DevTools → **Network**
2. 刷新页面，点开任意发往 `api.manus.im` 或 `manus.im` 的请求
3. Request Headers 里找到 `Cookie:`，复制其中 `session_id=...` 那一段（到下一个 `;` 为止）

**方式 C — 自动脚本（本机已登录时）**

```bash
node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs
eval "$(node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs --export)"
```

从 CDP `:9222` 或 Chrome Default Cookies 拉取；成功后再开 agent。失败则用方式 A/B。

**方式 D — 本机 Default Chrome 已登录（agent 侧）**

若用户说「Default profile 里有」，agent 先跑 `fetch-session.cjs --force-fetch`；失败再退回方式 A/B。

### How to give（交给 agent）

任选一种，**优先自动脚本 / 环境变量**（不用把 JWT 贴进聊天）：

| 方式 | 用户怎么做 | Agent 怎么用 |
|------|------------|--------------|
| **自动脚本（推荐）** | `node …/fetch-session.cjs` 然后 `eval "$(… --export)"` | 先跑 fetch；再注入 |
| **环境变量** | `export MANUS_SESSION_TOKEN='eyJ…'` 或 `MANUS_COOKIE='session_id=eyJ…'` | `resolve-session.cjs` / `process.env` |
| **shell 一次性** | 把变量写进当前 Cursor/终端会话环境 | 同上 |
| **本地文件** | `printf '%s' 'eyJ…' > /tmp/manus_session_id.value && chmod 600 …` | 读文件 / helper |
| **只贴 JWT** | 聊天里贴 Value | 写入 `/tmp/…` 再注入；**勿回显** |
| **JSON** | 见下方模板 | `addCookies` |
| **Cookie 头片段** | `session_id=eyJ…` | 解析后注入 |

环境变量约定：

| Var | Content |
|-----|---------|
| `MANUS_SESSION_TOKEN` | raw JWT only |
| `MANUS_COOKIE` | `session_id=…` or full `Cookie:` header |
| `MANUS_SESSION_FILE` | path to file with JWT or `session_id=…` (default `/tmp/manus_session_id.value`) |

示例（用户本地终端，**不要**提交进 git / `.env` 入库）：

```bash
# 自动（本机已登录 + CDP 或 Chrome Cookies）：
node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs
eval "$(node .cursor/skills/manus-official-cdp/scripts/fetch-session.cjs --export)"

# 或手动从 DevTools 复制 Value 后：
export MANUS_SESSION_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…'
export MANUS_COOKIE='session_id=eyJ…'

# 自检（只看长度，不打印 token）：
node .cursor/skills/manus-official-cdp/scripts/resolve-session.cjs
```

若 Cursor Agent 读不到你刚 `export` 的变量：在 **同一终端会话** 启动 agent，或把变量写进该会话的环境；必要时改用文件 `/tmp/manus_session_id.value`。

推荐 JSON 模板（聊天粘贴用，可只填 `value`）：

```json
{
  "name": "session_id",
  "value": "PASTE_JWT_HERE",
  "domain": ".manus.im",
  "path": "/"
}
```

Agent 解析到 token 后应立刻：

1. 优先已有 env；否则写入 `/tmp/manus_session_id.value`（`0600`），**不要**把完整 JWT 再复述回聊天
2. CDP `addCookies` → `GetAvailableCredits` Bearer 验 200 → 打开 `/app`
3. 确认成功时只回报：`source` / `valueLen` / `api status` / 最终 URL

提醒用户：这是登录凭证；用完可 `unset MANUS_SESSION_TOKEN MANUS_COOKIE`；**不要**发到公开渠道 / 不要提交 git。

## Critical cookie

| Field | Value |
|-------|--------|
| `name` | `session_id` |
| `domain` | `.manus.im` |
| `path` | `/` |
| shape | JWT (`eyJ…`, ≥2 dots) |

Optional: `login_success=1` on `manus.im` (not the real auth).

API check (Bearer = raw JWT):

```bash
TOKEN="$(node .cursor/skills/manus-official-cdp/scripts/resolve-session.cjs --token)"
curl -sS -X POST 'https://api.manus.im/user.v1.UserService/GetAvailableCredits' \
  -H 'content-type: application/json' \
  -H 'connect-protocol-version: 1' \
  -H "authorization: Bearer ${TOKEN}" \
  -H 'origin: https://manus.im' \
  -d '{}'
# expect HTTP 200 + totalCredits
unset TOKEN
```

## Workflow

```
Manus CDP session:
- [ ] 0. `fetch-session.cjs` (or resolve env/file) → else instruct user
- [ ] 1. Ensure CDP Chrome on :9222 (or start sticky profile)
- [ ] 2. Inject session_id if not already on context
- [ ] 3. Verify GetAvailableCredits → 200
- [ ] 4. Open https://manus.im/app ; handle /unavailable if geo-blocked
- [ ] 5. Hand off to replicate-manus-ui mining
```

### 1. Start or attach CDP Chrome

Sticky empty profile (cookie will be injected):

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-manus-cdp \
  --profile-directory=Default \
  --no-first-run --no-default-browser-check \
  "https://manus.im/app"
```

If `:9222` already answers `json/version`, **attach** — do not start another Chrome on the same port.

Drive with playwright-core (`/tmp/pw` or project `tmp/pw`):

```js
const { chromium } = require('/tmp/pw/node_modules/playwright-core')
const browser = await chromium.connectOverCDP('http://127.0.0.1:9222')
const context = browser.contexts()[0]
```

`browser.close()` on a CDP connection **disconnects only** — it does not quit Chrome.

### 2. Get / inject `session_id`

**First:** run the resolve helper (env / file). If `ok`, inject that JWT.

**Else:** CDP profile that already has cookies — read via Playwright:

```js
const cookies = await context.cookies(['https://manus.im'])
const session = cookies.find(c => c.name === 'session_id')
```

**Inject** (from env/file/user):

```js
const { execFileSync } = require('child_process')
const value = execFileSync('node', [
  '.cursor/skills/manus-official-cdp/scripts/resolve-session.cjs',
  '--token',
], { encoding: 'utf8' }).trim()

await context.addCookies([{
  name: 'session_id',
  value,
  domain: '.manus.im',
  path: '/',
  expires: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 30,
  httpOnly: false,
  secure: false,
  sameSite: 'Lax',
}])
```

macOS Default DB path (encrypted at rest):

`~/Library/Application Support/Google/Chrome/Default/Cookies`

Decrypt only if env/CDP cannot see the cookie; prefer env + Playwright `context.cookies()` over hand-decrypt.

### 3. Verify auth before trusting the UI

1. `session_id` present, JWT-shaped, `valueLen` ~300+
2. `GetAvailableCredits` with `Authorization: Bearer <jwt>` → **200**
3. Then navigate:

```js
const page = context.pages()[0] || await context.newPage()
await page.goto('https://manus.im/app', { waitUntil: 'domcontentloaded', timeout: 45000 })
await page.waitForTimeout(3000)
```

Success signals: URL stays on `/app` (or session deep link), title ~`Manus`, sidebar / `#manus-chat-box` / composer present, **not** `/login`.

### 4. Geo / unavailable

If URL or body shows **`/unavailable`** / 「Manus 在你所在的地区不可用」:

- Cookie may still be valid (API 200) — **do not** treat as login failure
- Need a network path that manus.im allows (VPN / different egress), then retry `/app` with the same cookie
- Re-check after network change; do not rotate JWT unless API returns 401

### 5. Hand off

Once `/app` is logged-in and interactive → follow **replicate-manus-ui** for DOM dumps, screenshots under `tmp/screenshots/` (gitignored). 「截图发过来」→ personal **telegram-screenshots**.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| API 401 `missing authorization header` | Sent Cookie only | Use `Bearer` JWT |
| API 401 unauthenticated | Expired / revoked session | Fresh Default login; re-copy `session_id` |
| `/login` after goto | Cookie missing / wrong domain | Inject `.manus.im` `session_id`; reload |
| `/unavailable` + API 200 | Region block | Change egress; keep same cookie |
| `:9222` empty / no pages | Tab closed; only extension SW | `context.newPage()` then goto `/app` |
| Profile lock / Chrome won’t start | Default profile already open | Use `/tmp/chrome-manus-cdp` + inject, or attach existing CDP |

## Security checklist

- [ ] No JWT in git, PR, skill files, or agent transcripts if avoidable
- [ ] Temp token files mode `0600`, path under `/tmp`, delete when done
- [ ] Chat replies: `hasSession` / `valueLen` / `api status` only
