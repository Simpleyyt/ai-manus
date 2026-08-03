# Backend Status Channel Unification (Approach A)

**Date:** 2026-08-03  
**Status:** Approved for implementation  
**Scope:** Make wire `status_update` the sole live authority for session phase; align with frontend `useSessionPhase`.

## Problem

Session phase is driven by overlapping sources:

1. Domain events `wait` / `done` / `error` (business + timeline)
2. Synthetic WS `status_update` (intended authority for busy/footer)
3. REST `session.status` (hydrate)

Frontend #201 still calls `noteDomainEvent('wait'|'done')` as a defense when `status_update` is late or dropped. That re-creates dual writers after we extracted `useSessionPhase`.

Backend already (via #200):

- Sends `status_update` **before** `stream_end`
- Prefers Mongo `WAITING` over stream-local `saw_error`

Gap: **`WaitEvent` does not emit a mid-stream `status_update(waiting)`**, so the client must either wait for stream end or keep domain→phase fallbacks.

## Goal

- Live phase: **only** `status_update` (+ REST hydrate + optimistic local run)
- Domain `wait` / `done` / `error` remain on the wire for timeline / copy; they **do not** drive phase on the client
- When `WaitEvent` is forwarded, immediately emit `status_update(waiting)` so waiting UI works before `stream_end`

### Non-goals

- Moving UI enrichment out of `AgentTaskRunner` (Approach B)
- Splitting live-only events from `AgentEvent` union (Approach C)
- Introducing a new `PhaseEvent` domain type

## Design

### Authority table

| Source | Drives phase? | Role |
|--------|---------------|------|
| REST `session.status` | Yes (hydrate only) | Refresh / idle join |
| `status_update` | Yes (live) | Sole live authority |
| Optimistic `chat()` | Yes (local) | Instant busy |
| Domain `wait` / `done` / `error` | **No** (after this work) | Timeline / assistant error bubble |

### Backend (`chat_ws.stream_session`)

After `await send_agent_event(session_id, event)`:

```python
if getattr(event, "type", None) == "wait":
    await send_status_update(session_id, "waiting")
```

Rationale: Runner sets Mongo `WAITING` before/as `WaitEvent` is queued; Domain yields `wait` then breaks. Emitting status immediately matches Mongo and unblocks the UI without waiting for the end-of-stream status block.

End-of-stream logic from #200 stays:

1. Resolve final status from Mongo (`waiting` > `saw_error` > mapped session status)
2. `status_update(final)`
3. `stream_end`

Optional (out of scope unless cheap): mid-stream `status_update(completed)` on `done` — not required if end-of-stream always fires.

### Frontend

[`ChatPage.vue`](../../../frontend/src/pages/ChatPage.vue):

- `handleEvent`: stop calling `noteDomainEvent('wait'|'done')`
- Keep `onStreamError → noteDomainEvent('error')` **or** remove and rely on end-of-stream `status_update(error|completed)` — prefer **remove** for purity; accept that busy clears on status_update (already before stream_end). Error assistant bubbles still come from `useAgentEvents` timeline.
- `showTakeControlBanner` already uses `phase === 'waiting' && !isBusy` — works once mid-stream waiting status arrives

[`useSessionPhase.ts`](../../../frontend/src/composables/useSessionPhase.ts):

- Keep `noteDomainEvent` API for unit tests / rare defense; ChatPage production path stops using wait/done/error notes
- Update / add a comment that live phase authority is `applyStatusUpdate`

Tests:

- Backend: if no pytest for WS, add a focused unit test of the helper that maps “after wait event → should emit waiting status” **or** document manual e2e with `chat_page_parity_e2e.yaml`
- Frontend: adjust ChatPage if any; keep `useSessionPhase` unit tests for `noteDomainEvent` as library behavior; add/adjust a test that documents production relies on `applyStatusUpdate('waiting')`

### Success criteria

- After `message_ask_user` → `WaitEvent`, client receives `status_update(waiting)` **before** `stream_end`
- ChatPage has no `noteDomainEvent('wait'|'done')` (and preferably no error note) on the live path
- TakeControlBanner / waiting footer appear without reload when browser tool + waiting
- `npm run test && type-check` (frontend); backend smoke or existing tests still pass

## Rollout

1. Backend mid-stream waiting status  
2. Frontend remove domain→phase notes on live path  
3. Verify with mock e2e yaml or manual session  
4. PR against `main`
