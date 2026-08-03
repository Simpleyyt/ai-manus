import { ref, computed, type Ref } from 'vue'
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

/**
 * Session phase view-model: busy flag + footer/thinking derived from a single
 * phase FSM. Live phase authority is WS `status_update` (+ REST hydrate +
 * optimistic run). `noteDomainEvent` remains for client/transport failures only.
 *
 * @see docs/superpowers/specs/2026-08-03-backend-status-channel-design.md
 */
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
