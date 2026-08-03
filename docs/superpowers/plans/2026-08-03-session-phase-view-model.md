# Session Phase View-Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract `useSessionPhase` so ChatPage binds derived busy/footer UI instead of owning `isLoading` + `sessionStatus` transition rules.

**Architecture:** New composable owns phase FSM (`pending|running|waiting|completed|error`) and `isBusy`; `useAgentEvents` becomes a pure timeline projector (optional error callback only); ChatPage wires WS/REST into phase + timeline and binds template flags.

**Tech Stack:** Vue 3 Composition API + TypeScript, Vitest, existing `SessionStatus` / `AgentStatus` / `Message` types.

**Spec:** `docs/superpowers/specs/2026-08-03-session-phase-view-model-design.md`

## Global Constraints

- Frontend only — no backend / chat WS protocol changes
- Port ChatPage footer/thinking semantics verbatim (including `status_update(error)` → treat like completed when was running/pending)
- Hydrate: REST status is phase source of truth; do **not** `noteDomainEvent` while replaying `session.events`
- Live: `wait` → phase waiting + ¬busy even if trailing `status_update` is dropped
- Drop message/tool/step → RUNNING inference (rely on optimistic run + `status_update`)
- Verify: `cd frontend && npm run test && npm run type-check && npm run lint`
- Do not commit unless the user asks (or the executing session explicitly includes commits)

## File structure

| File | Role |
|------|------|
| `frontend/src/composables/useSessionPhase.ts` | Phase FSM + derived UI flags |
| `frontend/src/composables/__tests__/useSessionPhase.spec.ts` | Unit tests for transitions |
| `frontend/src/composables/useAgentEvents.ts` | Timeline only; no `isLoading` writes |
| `frontend/src/pages/ChatPage.vue` | Wire phase + timeline; remove local FSM |
| `frontend/src/pages/SharePage.vue` | Stop passing `isLoading` into `useAgentEvents` |

---

### Task 1: `useSessionPhase` + failing tests

**Files:**
- Create: `frontend/src/composables/useSessionPhase.ts`
- Create: `frontend/src/composables/__tests__/useSessionPhase.spec.ts`

**Interfaces:**
- Consumes: `AgentStatus` from `frontend/src/types/event.ts`; `SessionStatus` from `frontend/src/types/response.ts`; `Message` / `MessageContent` / `AttachmentsContent` from `frontend/src/types/message.ts`
- Produces:

```ts
export type SessionPhase = 'pending' | 'running' | 'waiting' | 'completed' | 'error'

export function useSessionPhase(options?: {
  messages?: Ref<Message[]>
}): {
  phase: Ref<SessionPhase | undefined>
  isBusy: Ref<boolean>
  hydrateFromSessionStatus: (status: SessionStatus | string) => void
  applyStatusUpdate: (agentStatus: AgentStatus) => void
  noteOptimisticRun: () => void
  noteDomainEvent: (event: 'wait' | 'done' | 'error') => void
  reset: () => void
  showWaitingContinue: ComputedRef<boolean>
  showTaskCompleted: ComputedRef<boolean>
  showThinking: ComputedRef<boolean>
}
```

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/composables/__tests__/useSessionPhase.spec.ts`:

```ts
import { describe, it, expect, ref } from 'vitest'
import { ref as vueRef } from 'vue'
import { useSessionPhase } from '../useSessionPhase'
import { SessionStatus } from '../../types/response'
import type { Message } from '../../types/message'

describe('useSessionPhase', () => {
  it('hydrate waiting → not busy, showWaitingContinue', () => {
    const { hydrateFromSessionStatus, isBusy, phase, showWaitingContinue } = useSessionPhase()
    hydrateFromSessionStatus(SessionStatus.WAITING)
    expect(phase.value).toBe('waiting')
    expect(isBusy.value).toBe(false)
    expect(showWaitingContinue.value).toBe(true)
  })

  it('optimistic run then status waiting → waiting, not busy', () => {
    const { noteOptimisticRun, applyStatusUpdate, phase, isBusy, showWaitingContinue } =
      useSessionPhase()
    noteOptimisticRun()
    expect(phase.value).toBe('running')
    expect(isBusy.value).toBe(true)
    applyStatusUpdate('waiting')
    expect(phase.value).toBe('waiting')
    expect(isBusy.value).toBe(false)
    expect(showWaitingContinue.value).toBe(true)
  })

  it('noteDomainEvent wait without status_update → waiting, not busy', () => {
    const { noteOptimisticRun, noteDomainEvent, phase, isBusy } = useSessionPhase()
    noteOptimisticRun()
    noteDomainEvent('wait')
    expect(phase.value).toBe('waiting')
    expect(isBusy.value).toBe(false)
  })

  it('running shows thinking until visible assistant/tool/step after last user', () => {
    const messages = vueRef<Message[]>([
      { type: 'user', content: { content: 'hi', timestamp: 1 } },
    ])
    const { applyStatusUpdate, showThinking } = useSessionPhase({ messages })
    applyStatusUpdate('running')
    expect(showThinking.value).toBe(true)
    messages.value.push({
      type: 'assistant',
      content: { content: 'hello', timestamp: 2 },
    })
    expect(showThinking.value).toBe(false)
  })

  it('completed + assistant text → showTaskCompleted', () => {
    const messages = vueRef<Message[]>([
      { type: 'assistant', content: { content: 'done text', timestamp: 1 } },
    ])
    const { applyStatusUpdate, showTaskCompleted, isBusy } = useSessionPhase({ messages })
    applyStatusUpdate('completed')
    expect(isBusy.value).toBe(false)
    expect(showTaskCompleted.value).toBe(true)
  })

  it('error while running → phase completed, not busy (legacy footer UX)', () => {
    const { noteOptimisticRun, applyStatusUpdate, phase, isBusy } = useSessionPhase()
    noteOptimisticRun()
    applyStatusUpdate('error')
    expect(phase.value).toBe('completed')
    expect(isBusy.value).toBe(false)
  })

  it('reset clears phase and busy', () => {
    const { noteOptimisticRun, reset, phase, isBusy } = useSessionPhase()
    noteOptimisticRun()
    reset()
    expect(phase.value).toBeUndefined()
    expect(isBusy.value).toBe(false)
  })
})
```

Fix imports if the project’s Vitest setup uses a different `ref` import path — prefer `import { ref } from 'vue'` and `import { describe, it, expect } from 'vitest'` only.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- src/composables/__tests__/useSessionPhase.spec.ts`

Expected: FAIL (module or exports missing)

- [ ] **Step 3: Implement `useSessionPhase`**

Create `frontend/src/composables/useSessionPhase.ts` with logic ported from ChatPage:

```ts
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { AgentStatus } from '../types/event'
import { SessionStatus } from '../types/response'
import type { Message, MessageContent, AttachmentsContent } from '../types/message'

export type SessionPhase = 'pending' | 'running' | 'waiting' | 'completed' | 'error'

function toPhase(status: string): SessionPhase | undefined {
  if (
    status === 'pending' ||
    status === 'running' ||
    status === 'waiting' ||
    status === 'completed' ||
    status === 'error'
  ) {
    return status
  }
  return undefined
}

export function useSessionPhase(options?: { messages?: Ref<Message[]> }) {
  const phase = ref<SessionPhase | undefined>(undefined)
  const isBusy = ref(false)
  const messages = options?.messages

  const hydrateFromSessionStatus = (status: SessionStatus | string) => {
    const p = toPhase(String(status))
    phase.value = p
    isBusy.value = p === 'running'
  }

  const applyStatusUpdate = (agentStatus: AgentStatus) => {
    if (agentStatus === 'running') {
      isBusy.value = true
      phase.value = 'running'
    } else if (agentStatus === 'waiting') {
      isBusy.value = false
      phase.value = 'waiting'
    } else if (agentStatus === 'pending') {
      isBusy.value = false
      phase.value = 'pending'
    } else if (agentStatus === 'error') {
      isBusy.value = false
      if (phase.value === 'running' || phase.value === 'pending') {
        phase.value = 'completed'
      }
    } else {
      isBusy.value = false
      phase.value = 'completed'
    }
  }

  const noteOptimisticRun = () => {
    phase.value = 'running'
    isBusy.value = true
  }

  const noteDomainEvent = (event: 'wait' | 'done' | 'error') => {
    if (event === 'wait') {
      phase.value = 'waiting'
      isBusy.value = false
    } else if (event === 'done') {
      phase.value = 'completed'
    } else {
      // Mirror legacy: clear busy; only flip phase when running/pending
      isBusy.value = false
      if (phase.value === 'running' || phase.value === 'pending') {
        phase.value = 'completed'
      }
    }
  }

  const reset = () => {
    phase.value = undefined
    isBusy.value = false
  }

  const showWaitingContinue = computed(
    () => phase.value === 'waiting' && !isBusy.value,
  )

  const lastAssistantPlainText = computed(() => {
    const list = messages?.value
    if (!list?.length) return ''
    for (let i = list.length - 1; i >= 0; i--) {
      if (list[i].type === 'assistant') {
        return ((list[i].content as MessageContent).content || '').trim()
      }
    }
    return ''
  })

  const showTaskCompleted = computed(
    () =>
      phase.value === 'completed' &&
      !!lastAssistantPlainText.value &&
      !isBusy.value,
  )

  // Port ChatPage showThinking verbatim (messages since last user turn)
  const showThinking = computed(() => {
    if (!isBusy.value) return false
    if (showWaitingContinue.value || showTaskCompleted.value) return false
    const list = messages?.value
    if (!list) return true

    let lastUserIdx = -1
    for (let i = list.length - 1; i >= 0; i--) {
      const m = list[i]
      if (m.type === 'user') {
        lastUserIdx = i
        break
      }
      if (m.type === 'attachments' && (m.content as AttachmentsContent).role === 'user') {
        lastUserIdx = i
        break
      }
    }

    for (let i = lastUserIdx + 1; i < list.length; i++) {
      const m = list[i]
      if (m.type === 'tool' || m.type === 'step') return false
      if (m.type === 'assistant') {
        const text = ((m.content as MessageContent).content || '').trim()
        if (text) return false
      }
    }
    return true
  })

  return {
    phase,
    isBusy,
    hydrateFromSessionStatus,
    applyStatusUpdate,
    noteOptimisticRun,
    noteDomainEvent,
    reset,
    showWaitingContinue,
    showTaskCompleted,
    showThinking,
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- src/composables/__tests__/useSessionPhase.spec.ts`

Expected: all PASS

- [ ] **Step 5: Commit** (only if user asked for commits)

```bash
git add frontend/src/composables/useSessionPhase.ts \
  frontend/src/composables/__tests__/useSessionPhase.spec.ts
git commit -m "feat(frontend): add useSessionPhase view-model"
```

---

### Task 2: Purify `useAgentEvents`

**Files:**
- Modify: `frontend/src/composables/useAgentEvents.ts`
- Modify: `frontend/src/pages/SharePage.vue` (call site only in this task if trivial; otherwise Task 3)

**Interfaces:**
- Consumes: existing event types
- Produces: `AgentEventState` **without** `isLoading`; `AgentEventOptions` gains `onStreamError?: () => void` called from error + step failed handlers

- [ ] **Step 1: Update types and stop writing loading**

In `useAgentEvents.ts`:

1. Remove `isLoading` from `AgentEventState`.
2. Add to `AgentEventOptions`:

```ts
  /** Fired when stream shows an error assistant bubble or step failed — page maps to phase. */
  onStreamError?: () => void
```

3. In `handleStepEvent` for `failed`: remove `isLoading.value = false`; call `options.onStreamError?.()`.
4. In `handleErrorEvent`: remove `isLoading.value = false`; call `options.onStreamError?.()`; keep pushing the assistant error message.

- [ ] **Step 2: Fix SharePage call site**

In `SharePage.vue`, remove `isLoading` from the object passed into `useAgentEvents`. If SharePage still declares a local `isLoading` only for the composable, delete that binding if unused; do not add `useSessionPhase` to SharePage in this PR.

- [ ] **Step 3: Type-check**

Run: `cd frontend && npm run type-check`

Expected: PASS (ChatPage will still fail until Task 3 — if type-check is project-wide and ChatPage still passes `isLoading`, either do Task 3 immediately after or temporarily leave a deprecated optional `isLoading?: Ref<boolean>` unused in the state type for one commit. Prefer completing Task 3 in the same working tree before declaring green.)

**Preferred sequencing:** finish Task 2 edits then immediately Task 3 so `type-check` is green once.

- [ ] **Step 4: Commit** (if user asked)

```bash
git add frontend/src/composables/useAgentEvents.ts frontend/src/pages/SharePage.vue
git commit -m "refactor(frontend): keep useAgentEvents timeline-only"
```

---

### Task 3: Wire `ChatPage` to `useSessionPhase`

**Files:**
- Modify: `frontend/src/pages/ChatPage.vue`

**Interfaces:**
- Consumes: `useSessionPhase({ messages })` from Task 1; purified `useAgentEvents` from Task 2
- Produces: template still uses `showThinking` / `showWaitingContinue` / `showTaskCompleted` / busy for ChatBox — sourced from phase composable

- [ ] **Step 1: Instantiate phase next to messages**

After `messages` ref exists (from `toRefs(state)`):

```ts
const {
  phase,
  isBusy,
  hydrateFromSessionStatus,
  applyStatusUpdate,
  noteOptimisticRun,
  noteDomainEvent,
  reset: resetPhase,
  showWaitingContinue,
  showTaskCompleted,
  showThinking,
} = useSessionPhase({ messages })
```

- Alias for minimal template churn: either replace every `isLoading` with `isBusy`, or `const isLoading = isBusy`. Prefer **replace with `isBusy`** in script and template `:isRunning="isBusy"`.
- Remove local `sessionStatus` ref; use `phase` everywhere `sessionStatus` was compared (map string equality: `phase.value === 'waiting'` etc.). For any code that still needs `SessionStatus` enum (e.g. comparisons), compare `phase.value === SessionStatus.WAITING` only if values match — they do (`'waiting'` etc.).

- [ ] **Step 2: Delete local FSM**

Remove from ChatPage:
- `applyAgentStatus` function
- Local `showWaitingContinue` / `showTaskCompleted` / `showThinking` computeds
- In `handleEvent`: status writes for done/wait/message/tool/step — replace with:

```ts
const handleEvent = (event: AgentEvent) => {
  handleAgentEvent(event)
  if (event.event === 'status_update') return
  if (event.event === 'wait') noteDomainEvent('wait')
  else if (event.event === 'done') noteDomainEvent('done')
  else if (event.event === 'error') noteDomainEvent('error')
}
```

- `useAgentEvents` options:

```ts
{
  onToolActivity: (tool) => { /* unchanged computer panel */ },
  onStreamError: () => noteDomainEvent('error'),
}
```

- [ ] **Step 3: Wire callbacks / restore / reset**

- `chatStreamCallbacks.onStatusUpdate` → `applyStatusUpdate(agentStatus)`
- `chat()` / `onOpen` optimistic → `noteOptimisticRun()` instead of `isLoading.value = true`
- `onError` callback → `noteDomainEvent('error')` (or `isBusy` clear via noteDomainEvent)
- `restoreSession`:

```ts
hydrateFromSessionStatus(session.status)
for (const event of session.events) {
  handleAgentEvent(event)  // timeline only — NOT handleEvent (no noteDomainEvent)
}
// then join WS as today; if RUNNING, noteOptimisticRun() or rely on status_update(running)
```

Important: use `handleAgentEvent` for hydrate replay, not `handleEvent`, so domain wait/done in history do not override REST phase.

- `resetState`: call `resetPhase()` instead of `sessionStatus.value = undefined`; remove `isLoading` from `createInitialState` **or** keep the field but stop using it (cleaner: remove from initial state and all `toRefs` if nothing else needs it).

- Any remaining `sessionStatus.value === SessionStatus.RUNNING` (e.g. copy-actions helpers) → `phase.value === 'running'` / `isBusy`.

- [ ] **Step 4: Verify**

Run:

```bash
cd frontend && npm run test && npm run type-check && npm run lint
```

Expected: all green.

Manual smoke (dev stack):
1. Open completed session → task completed footer if assistant text exists  
2. Open waiting session → waiting continue row, ChatBox not running  
3. Send message → thinking until first tool/assistant text; stop button while busy  

- [ ] **Step 5: Commit** (if user asked)

```bash
git add frontend/src/pages/ChatPage.vue frontend/src/composables/useAgentEvents.ts \
  frontend/src/pages/SharePage.vue
git commit -m "refactor(frontend): ChatPage uses useSessionPhase for session UX state"
```

---

### Task 4: Spec status + PR hygiene

**Files:**
- Modify: `docs/superpowers/specs/2026-08-03-session-phase-view-model-design.md` — set **Status:** approved / implemented

- [ ] **Step 1:** Update status line at top of the design doc to `implemented` (or `approved` if PR not merged yet).
- [ ] **Step 2:** Ensure branch is based on latest `main` (or `feat/chat-page-parity` if TakeControlBanner must coexist — default **base `main`**; banner work stays in #199).
- [ ] **Step 3:** Open PR summarizing view-model extraction + test plan from Global Constraints.

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| `useSessionPhase` FSM + isBusy | Task 1 |
| Derived showWaiting / showCompleted / showThinking | Task 1 |
| Unit tests (6+ cases) | Task 1 |
| `useAgentEvents` no isLoading writes | Task 2 |
| Optional error callback | Task 2 |
| SharePage drop isLoading coupling | Task 2 |
| ChatPage bind-only; remove applyAgentStatus | Task 3 |
| Hydrate without noteDomainEvent | Task 3 |
| Live wait/done/error → noteDomainEvent | Task 3 |
| No protocol / takeover registry | Out of scope (noted) |

## Placeholder / consistency self-review

- Method names aligned: `hydrateFromSessionStatus`, `applyStatusUpdate`, `noteOptimisticRun`, `noteDomainEvent`, `reset`  
- `SessionPhase` includes `error` but live `applyStatusUpdate('error')` maps to `completed` when was running/pending — matches ChatPage legacy  
- No TBD steps
