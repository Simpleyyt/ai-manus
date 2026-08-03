# Session Phase View-Model (Frontend Decoupling)

**Date:** 2026-08-03  
**Status:** implemented  
**Scope:** Frontend only (Approach A). No WS protocol or backend changes in this work.

## Problem

[`ChatPage.vue`](../../../frontend/src/pages/ChatPage.vue) currently owns three jobs at once:

1. **Wire consumer** — `chatWithSession` callbacks, `status_update`, domain events  
2. **Session state machine** — `isLoading` + `sessionStatus` written from REST restore, optimistic send, `wait`/`done`, message/tool/step inference, and `applyAgentStatus`  
3. **UI orchestration** — thinking / waiting footer / task completed / ChatBox stop, plus Computer panel side effects  

[`useAgentEvents.ts`](../../../frontend/src/composables/useAgentEvents.ts) is mostly a timeline projector, but also mutates `isLoading` on step failed / error — a second writer on the same busy flag.

Symptoms: late `stream_end` clearing handlers before `status_update`, `wait` vs loading races, and hard-to-test footer visibility (`showThinking` / `showWaitingContinue` / `showTaskCompleted`).

## Goal

Extract a **Session phase view-model** so ChatPage (and later Share/other surfaces) only bind derived UI. Timeline projection stays pure; phase is the single authority for busy/footer.

### Success criteria

- One module owns phase transitions; ChatPage does not call `sessionStatus.value = …` or ad-hoc `isLoading` rules except via the view-model API  
- `useAgentEvents` does not write loading/busy  
- Unit tests cover phase transitions without mounting ChatPage  
- Behavior parity: thinking spacer, waiting continue row, task completed footer, ChatBox `isRunning` match current ChatPage on main (+ wait→clear busy from #200 if merged)

### Non-goals (this spec)

- Backend / chat WS protocol changes (covered by #200)  
- Tool capability registry / `name === 'browser'` takeover rules  
- Merging chat join/leave into a god `useChatSession`  
- Rewriting SharePage beyond “timeline stays independent of phase”

## Current data flow (relevant slice)

```
REST getSession.status ──► sessionStatus (initial)
chat() optimistic       ──► isLoading = true
status_update           ──► applyAgentStatus (intended authority)
domain wait/done/…      ──► handleEvent mutates sessionStatus (+ wait clears isLoading)
useAgentEvents error    ──► isLoading = false
stream_end / onClose    ──► clears handlers only (loading relies on status_update)
```

Derived UI today:

| Flag | Rule (simplified) |
|------|-------------------|
| `showWaitingContinue` | status === waiting ∧ ¬loading |
| `showTaskCompleted` | status === completed ∧ last assistant text ∧ ¬loading |
| `showThinking` | loading ∧ no visible output since last user turn ∧ ¬waiting/completed footers |
| ChatBox `isRunning` | `isLoading` |

## Design

### Modules

| Module | Responsibility | Must not |
|--------|----------------|----------|
| `useSessionPhase` (new) | Phase FSM + `isBusy` + footer/thinking derived flags (thinking may read `messages`) | Build Message list; open Computer panel |
| `useAgentEvents` | `AgentEvent` → `messages[]` / title / plan / lastTool | Touch busy/phase |
| `ChatPage.vue` | Wire callbacks → phase + timeline; bind template; Computer `onToolActivity` | Encode phase transition rules inline |

### Phase model

```ts
export type SessionPhase = 'pending' | 'running' | 'waiting' | 'completed' | 'error'

// Public surface (illustrative)
export function useSessionPhase() {
  // state
  phase: Ref<SessionPhase | undefined>
  isBusy: Ref<boolean>           // replaces isLoading for session-run UX

  // inputs
  hydrateFromSessionStatus(status: SessionStatus | string): void
  applyStatusUpdate(agentStatus: AgentStatus): void
  noteOptimisticRun(): void      // chat() / onOpen
  noteDomainEvent(event: 'wait' | 'done' | 'error'): void
  // optional: noteActivity() if we still infer running from message/tool/step
  reset(): void

  // derived (may take messages Ref for thinking)
  showWaitingContinue: ComputedRef<boolean>
  showTaskCompleted: ComputedRef<boolean>  // needs lastAssistantPlainText or messages
  showThinking: ComputedRef<boolean>
}
```

Map wire/REST strings 1:1 where possible (`AgentStatus` / `SessionStatus` → `SessionPhase`). Keep exporting `isBusy` as the ChatBox `isRunning` source so renames stay localized.

### Transition priority (authoritative order)

1. **`applyStatusUpdate`** — same semantics as today’s `applyAgentStatus`  
   - `running` → phase `running`, busy true  
   - `waiting` → phase `waiting`, busy false  
   - `pending` → phase `pending`, busy false  
   - `completed` → phase `completed`, busy false  
   - `error` → busy false; if phase was `running`|`pending` → `completed` (preserve today’s footer UX; do not invent a new error footer in this PR unless already shown)
2. **`noteDomainEvent('wait')`** → phase `waiting`, busy false (defense if status_update dropped after stream_end)  
3. **`noteDomainEvent('done')`** → phase `completed`  
4. **`noteOptimisticRun` / onOpen** → phase `running`, busy true  
5. **`hydrateFromSessionStatus`** on restore — set phase from REST; busy true only if status is `running` (match restoreSession)

**Drop or narrow:** ChatPage today sets `sessionStatus = RUNNING` on message/tool/step when not waiting. Prefer letting `status_update(running)` + optimistic run cover this. If restore replay of historical events would incorrectly flip phase, **do not** re-apply activity→running during hydrate replay (only apply wait/done domain notes if needed for parity, or skip domain phase notes while `hydrating`).

Recommended hydrate algorithm:

```
hydrateFromSessionStatus(session.status)
for event of session.events:
  handleAgentEvent(event)          // timeline only
  // do NOT noteDomainEvent during hydrate — REST status is source of truth
join WS…
```

Live stream:

```
onStatusUpdate → applyStatusUpdate
onMessage:
  if terminal/file_update → eventBus (unchanged)
  else → handleAgentEvent + if wait|done|error → noteDomainEvent
onOpen / chat() → noteOptimisticRun
onClose → clear cancel handle only (unchanged; busy follows phase)
```

### `useAgentEvents` change

- Remove `isLoading` from `AgentEventState` (or leave unused and deprecate).  
- On step `failed` / `error` event: call optional `onError?: () => void` / `onStepFailed?: () => void` so the page can `noteDomainEvent('error')` — **or** emit nothing and rely on `status_update`. Prefer optional callback for parity with today’s immediate `isLoading = false` on tool error text.  
- SharePage: stop passing `isLoading` into the composable (SharePage can keep a local unused ref or omit).

### ChatPage binding

Template keeps the same flags, sourced from `useSessionPhase`:

- `:isRunning="isBusy"`  
- `v-if="showThinking"` / waiting / completed components unchanged  

Remove local `applyAgentStatus`, inline wait/done status writes, and the three show* computeds (move into composable or thin wrappers).

### Tests

New: `frontend/src/composables/__tests__/useSessionPhase.spec.ts`

Cases (minimum):

1. hydrate `waiting` → ¬busy, `showWaitingContinue`  
2. `noteOptimisticRun` then `applyStatusUpdate('waiting')` → waiting, ¬busy  
3. `noteDomainEvent('wait')` without status_update → waiting, ¬busy  
4. `applyStatusUpdate('running')` then thinking true until a non-empty assistant/tool/step appears in provided messages  
5. `applyStatusUpdate('completed')` + assistant text → `showTaskCompleted`  
6. `applyStatusUpdate('error')` while running → phase completed (legacy behavior), ¬busy  

Optional: one ChatPage-level smoke is out of scope; Vitest unit tests are enough for this PR.

### Files

| Path | Action |
|------|--------|
| `frontend/src/composables/useSessionPhase.ts` | Create |
| `frontend/src/composables/__tests__/useSessionPhase.spec.ts` | Create |
| `frontend/src/composables/useAgentEvents.ts` | Stop writing isLoading; optional error callback |
| `frontend/src/composables/__tests__/*` for useAgentEvents | Adjust if they assert isLoading |
| `frontend/src/pages/ChatPage.vue` | Wire to useSessionPhase |
| `frontend/src/pages/SharePage.vue` | Drop isLoading coupling to useAgentEvents only |

### Rollout

1. Land `useSessionPhase` + tests  
2. Switch ChatPage  
3. Clean useAgentEvents + SharePage  
4. Manual: restore waiting session, send message to wait (mock), completed footer, thinking → first tool  

## Risks

| Risk | Mitigation |
|------|------------|
| Hydrate replay double-applies wait/done | Skip domain phase notes while hydrating; trust REST status |
| Thinking false negatives after refactor | Port existing showThinking logic verbatim into composable with messages ref |
| error status UX subtlety | Copy applyAgentStatus error branch exactly |
| Naming churn (`isLoading` vs `isBusy`) | Keep `isBusy` internally; alias `isLoading` export if needed for smaller ChatPage diff |

## Follow-ups (not this PR)

- Tool capability map for takeover banner (`browser`)  
- Protocol-level single status channel (backend)  
- Optional `useChatSession` façade later once phase + timeline are stable
