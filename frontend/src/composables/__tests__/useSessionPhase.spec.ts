import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
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
    const messages = ref<Message[]>([
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
    const messages = ref<Message[]>([
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
