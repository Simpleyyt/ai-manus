import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useSessionPhase } from '../useSessionPhase'
import { SessionStatus } from '../../types/response'
import type { Message, MessageContent, StepContent, ToolContent } from '../../types/message'

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

  it('stale status_update running after waiting does not hide waiting footer', () => {
    const { applyStatusUpdate, phase, isBusy, showWaitingContinue } = useSessionPhase()
    applyStatusUpdate('waiting')
    applyStatusUpdate('running')
    expect(phase.value).toBe('waiting')
    expect(isBusy.value).toBe(false)
    expect(showWaitingContinue.value).toBe(true)
  })

  it('noteOptimisticRun then status running resumes from waiting', () => {
    const { applyStatusUpdate, noteOptimisticRun, phase, isBusy, showWaitingContinue } =
      useSessionPhase()
    applyStatusUpdate('waiting')
    noteOptimisticRun()
    applyStatusUpdate('running')
    expect(phase.value).toBe('running')
    expect(isBusy.value).toBe(true)
    expect(showWaitingContinue.value).toBe(false)
  })

  it('noteDomainEvent wait without status_update → waiting, not busy', () => {
    const { noteOptimisticRun, noteDomainEvent, phase, isBusy } = useSessionPhase()
    noteOptimisticRun()
    noteDomainEvent('wait')
    expect(phase.value).toBe('waiting')
    expect(isBusy.value).toBe(false)
  })

  it('running shows thinking until a live step/tool indicator exists', () => {
    const messages = ref<Message[]>([
      { type: 'user', content: { content: 'hi', timestamp: 1 } as MessageContent },
    ])
    const { applyStatusUpdate, showThinking } = useSessionPhase({ messages })
    applyStatusUpdate('running')
    expect(showThinking.value).toBe(true)

    // Notify text alone must not hide thinking — gaps before next tool still need it
    messages.value.push({
      type: 'assistant',
      content: { content: 'hello', timestamp: 2 } as MessageContent,
    })
    expect(showThinking.value).toBe(true)

    messages.value.push({
      type: 'step',
      content: {
        id: 's1',
        description: 'Do work',
        status: 'running',
        tools: [],
        timestamp: 3,
      } as StepContent,
    })
    expect(showThinking.value).toBe(false)

    ;(messages.value[2].content as StepContent).status = 'completed'
    expect(showThinking.value).toBe(true)
  })

  it('calling tool hides thinking; called tool brings it back while busy', () => {
    const messages = ref<Message[]>([
      { type: 'user', content: { content: 'hi', timestamp: 1 } as MessageContent },
    ])
    const { applyStatusUpdate, showThinking } = useSessionPhase({ messages })
    applyStatusUpdate('running')
    messages.value.push({
      type: 'tool',
      content: {
        tool_call_id: 't1',
        name: 'shell',
        function: 'shell_exec',
        args: {},
        status: 'calling',
        timestamp: 2,
      } as ToolContent,
    })
    expect(showThinking.value).toBe(false)
    ;(messages.value[1].content as ToolContent).status = 'called'
    expect(showThinking.value).toBe(true)
  })

  it('completed + assistant text → showTaskCompleted', () => {
    const messages = ref<Message[]>([
      { type: 'assistant', content: { content: 'done text', timestamp: 1 } as MessageContent },
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
