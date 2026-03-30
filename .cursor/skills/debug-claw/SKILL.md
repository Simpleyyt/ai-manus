---
name: debug-claw
description: >-
  Debug and test the OpenClaw (Claw) integration in ai-manus. Use when
  investigating Claw chat issues, history merge problems, file upload/download
  failures, WebSocket connectivity, or container startup errors.
---

# Debug Claw

## Architecture Overview

Claw has three data layers that interact during debugging:

| Layer | Location | Contains |
|-------|----------|----------|
| **MongoDB** | `manus.claws` collection | User/assistant messages, attachment metadata, claw status |
| **Claw .jsonl** | Container `~/.openclaw/agents/main/sessions/` | OpenClaw native session history (user/assistant/toolResult) |
| **manus-claw plugin** | Container `/home/node/.openclaw/plugins/manus-claw/` | Upload metadata cache, file resolver cache |

The backend merges MongoDB + .jsonl on every `/api/v1/claw/history` call.

## Dev Commands

```bash
# Build & restart
./dev.sh build              # all containers
./dev.sh build backend claw # specific containers
./dev.sh up -d
./dev.sh up -d backend      # restart single container

# Logs
./dev.sh log claw -n 30     # last 30 lines
./dev.sh log backend -n 30
docker compose -f docker-compose-development.yml logs -f claw  # follow
```

## Checking Data Sources

### 1. MongoDB (authoritative for attachments)

```bash
docker compose -f docker-compose-development.yml exec -T mongodb mongosh --quiet --eval '
var claw = db.getSiblingDB("manus").claws.findOne({user_id: "anonymous"});
if (!claw) { print("No claw found"); } else {
    var msgs = claw.messages || [];
    print("status=" + claw.status + " msgs=" + msgs.length);
    msgs.forEach(function(m, i) {
        print(i + " [" + m.role + "] ts=" + m.timestamp + " " + (m.content||"").substring(0,80));
    });
}'
```

### 2. Claw .jsonl (raw session history from container)

```bash
# Via manus-claw HTTP API (port 18788 on host)
curl -s 'http://localhost:18788/history?session_id=default&limit=20' | python3 -m json.tool
```

### 3. Merged result (what the frontend sees)

```bash
curl -s 'http://localhost:8000/api/v1/claw/history' | python3 -m json.tool
```

### Quick comparison script

```python
import json, urllib.request, subprocess

API = 'http://localhost:8000/api/v1'

# Source 1: claw .jsonl
claw = json.loads(urllib.request.urlopen('http://localhost:18788/history?session_id=default').read())
claw_msgs = claw['messages']
print(f"Claw: {len(claw_msgs)} messages")

# Source 2: merged API
merged = json.loads(urllib.request.urlopen(f'{API}/claw/history').read())['data']['messages']
print(f"Merged: {len(merged)} messages")

# Source 3: MongoDB
r = subprocess.run(['docker', 'compose', '-f', 'docker-compose-development.yml', 'exec', '-T', 'mongodb',
    'mongosh', '--quiet', '--eval',
    'var c=db.getSiblingDB("manus").claws.findOne({user_id:"anonymous"}); '
    'print(c ? (c.messages||[]).length : 0);'
], capture_output=True, text=True)
print(f"MongoDB: {r.stdout.strip()} messages")
```

## Testing Chat via WebSocket

```python
import asyncio, json, websockets

async def send_and_wait(message):
    uri = 'ws://localhost:8000/api/v1/claw/ws?token=none'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            'type': 'chat', 'message': message, 'session_id': 'default'
        }))
        response = ''
        while True:
            try:
                data = await asyncio.wait_for(ws.recv(), timeout=10)
                chunk = json.loads(data)
                if chunk.get('type') == 'text':
                    response += chunk.get('content', '')
                elif chunk.get('type') == 'done':
                    break
            except asyncio.TimeoutError:
                break
        print(f"Response: {response[:200]}")

asyncio.run(send_and_wait("你好"))
```

## Testing File Upload (Agent → User)

Send a message asking Claw to create and upload a file:

```python
# Ask claw to use manus_upload_file tool
asyncio.run(send_and_wait("创建一个 hello.txt 文件并发送给我"))
```

Then verify:
1. Check claw logs for `[manus_upload_file]` entries
2. Check merged history for `attachments` role messages
3. Check upload metadata cache: `docker exec ai-manus-claw-1 ls /home/node/.openclaw/plugins/manus-claw/upload_meta/`

## Testing File Download (User → Agent)

Send a file via WebSocket with `file_ids`:

```python
await ws.send(json.dumps({
    'type': 'chat',
    'message': '看看这个文件',
    'session_id': 'default',
    'file_ids': ['<gridfs_file_id>']
}))
```

Then verify:
1. Backend log: `[claw-ws] pushed {filename} to workspace`
2. Claw workspace: `docker exec ai-manus-claw-1 ls /home/node/.openclaw/workspace/`
3. Message content should contain `<MANUS_FILE ... />` tags

## Testing History Merge (Dedup)

The most common issue. Test by sending identical messages then refreshing:

```python
# Send 3 identical messages, then call history twice
for i in range(3):
    asyncio.run(send_and_wait("重复消息"))

# Compare two consecutive refreshes
r1 = json.loads(urllib.request.urlopen(f'{API}/claw/history').read())['data']['messages']
r2 = json.loads(urllib.request.urlopen(f'{API}/claw/history').read())['data']['messages']
assert len(r1) == len(r2), f"Inconsistent: {len(r1)} vs {len(r2)}"
```

Key merge rules:
- Dedup uses `(role, timestamp±5s, content_prefix)` fingerprint matching
- Attachments dedup by `file_id` across sources
- DB messages are authoritative; claw fills gaps
- Empty assistant messages (tool-call intermediate steps) are filtered

## Testing Delete → Recreate Flow

```bash
# Delete (clears MongoDB, keeps container)
curl -X DELETE http://localhost:8000/api/v1/claw

# Recreate
curl -X POST http://localhost:8000/api/v1/claw

# History should recover text from .jsonl (attachments lost from MongoDB)
curl -s http://localhost:8000/api/v1/claw/history | python3 -c "
import json,sys; msgs=json.load(sys.stdin)['data']['messages']
print(f'Recovered: {len(msgs)} messages')
"
```

## Common Issues

| Symptom | Check | Fix |
|---------|-------|-----|
| Claw won't start | `./dev.sh log claw` for config errors | Check `claw/entrypoint.sh`, `openclaw.json` |
| Gateway handshake failed | Claw log for `invalid connect params` | Verify gateway-client.js `connect` message format |
| 500 on chat | Backend log for proxy errors | Check `OPENAI_API_KEY`, `OPENAI_BASE_URL` in env |
| Files not displayed after refresh | Compare MongoDB vs .jsonl attachments | Check `HttpClawClient.get_history()` parses `toolResult` |
| Duplicate messages after refresh | Run merge comparison script above | Check `_merge_histories` dedup logic in `claw_service.py` |
| `manus-file://` not resolved | Claw log for `[file-resolver]` | Check `/claw/resolve/{id}` endpoints, API key auth |
| WS not connected | Browser console, backend WS log | Check `_resolve_ws_user`, auth provider config |

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/application/services/claw_service.py` | Merge logic, chat processing, CRUD |
| `backend/app/infrastructure/external/claw/http_claw_client.py` | Parses claw .jsonl history |
| `backend/app/interfaces/api/claw_routes.py` | REST + WebSocket endpoints |
| `claw/manus-claw/src/gateway-bridge.js` | Gateway ↔ backend bridge, prompt processing |
| `claw/manus-claw/src/index.js` | Plugin entry, `manus_upload_file` tool |
| `claw/manus-claw/src/manus-file-resolver.js` | `manus-file://` URI resolution |
| `claw/manus-claw/src/http-server.js` | Claw HTTP API (chat, history, workspace) |
| `frontend/src/pages/ClawPage.vue` | Claw chat UI, WS handling, history loading |
