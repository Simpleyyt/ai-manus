import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useAgentEvents } from '../useAgentEvents'
import { isComputerPanelTool } from '../../constants/tool'
import type { Message, StepContent, ToolContent } from '../../types/message'
import type { PlanEventData, AgentEvent } from '../../types/event'

function makeToolEvent(overrides: Partial<{
  name: string
  function: string
  tool_call_id: string
  status: 'calling' | 'called'
}> = {}): AgentEvent {
  return {
    event: 'tool',
    data: {
      event_id: 'e1',
      timestamp: Math.floor(Date.now() / 1000),
      tool_call_id: overrides.tool_call_id ?? 'tc-1',
      name: overrides.name ?? 'file',
      function: overrides.function ?? 'file_write',
      args: { file: '/home/ubuntu/demo.txt' },
      status: overrides.status ?? 'calling',
      content: undefined,
    },
  } as AgentEvent
}

describe('isComputerPanelTool', () => {
  it('includes shell/file/browser/search/mcp', () => {
    expect(isComputerPanelTool('shell')).toBe(true)
    expect(isComputerPanelTool('file')).toBe(true)
    expect(isComputerPanelTool('browser')).toBe(true)
    expect(isComputerPanelTool('search')).toBe(true)
    expect(isComputerPanelTool('mcp')).toBe(true)
  })

  it('excludes soft-plan and message tools', () => {
    expect(isComputerPanelTool('todo')).toBe(false)
    expect(isComputerPanelTool('message')).toBe(false)
    expect(isComputerPanelTool(undefined)).toBe(false)
  })
})

describe('useAgentEvents computer follow', () => {
  it('ignores plan_report tool events in the chat timeline', () => {
    const messages = ref<Message[]>([])
    const title = ref('')
    const plan = ref<PlanEventData | undefined>()
    const lastEventId = ref<string | undefined>()
    const lastTool = ref<ToolContent | undefined>()
    const lastNoMessageTool = ref<ToolContent | undefined>()
    const activity: ToolContent[] = []

    const { handleEvent } = useAgentEvents(
      { messages, title, plan, lastEventId, lastTool, lastNoMessageTool },
      { onToolActivity: (t) => activity.push(t) },
    )

    handleEvent(makeToolEvent({
      name: 'todo',
      function: 'plan_report',
      tool_call_id: 'plan-report-1',
      status: 'called',
    }))

    expect(messages.value).toHaveLength(0)
    expect(lastTool.value).toBeUndefined()
    expect(lastNoMessageTool.value).toBeUndefined()
    expect(activity).toHaveLength(0)
  })

  it('ignores replan tool events in the chat timeline', () => {
    const messages = ref<Message[]>([])
    const title = ref('')
    const plan = ref<PlanEventData | undefined>()
    const lastEventId = ref<string | undefined>()
    const lastTool = ref<ToolContent | undefined>()
    const lastNoMessageTool = ref<ToolContent | undefined>()
    const activity: ToolContent[] = []

    const { handleEvent } = useAgentEvents(
      { messages, title, plan, lastEventId, lastTool, lastNoMessageTool },
      { onToolActivity: (t) => activity.push(t) },
    )

    handleEvent(makeToolEvent({
      name: 'todo',
      function: 'replan',
      tool_call_id: 'replan-1',
      status: 'called',
    }))

    expect(messages.value).toHaveLength(0)
    expect(lastTool.value).toBeUndefined()
    expect(lastNoMessageTool.value).toBeUndefined()
    expect(activity).toHaveLength(0)
  })

  it('ignores legacy todo tool events in the chat timeline', () => {
    const messages = ref<Message[]>([])
    const title = ref('')
    const plan = ref<PlanEventData | undefined>()
    const lastEventId = ref<string | undefined>()
    const lastTool = ref<ToolContent | undefined>()
    const lastNoMessageTool = ref<ToolContent | undefined>()
    const activity: ToolContent[] = []

    const { handleEvent } = useAgentEvents(
      { messages, title, plan, lastEventId, lastTool, lastNoMessageTool },
      { onToolActivity: (t) => activity.push(t) },
    )

    handleEvent(makeToolEvent({
      name: 'todo',
      function: 'todo_write',
      tool_call_id: 'todo-1',
      status: 'calling',
    }))

    expect(messages.value).toHaveLength(0)
    expect(lastTool.value).toBeUndefined()
    expect(lastNoMessageTool.value).toBeUndefined()
    expect(activity).toHaveLength(0)
  })

  it('seeds a running chat step from plan events', () => {
    const messages = ref<Message[]>([])
    const title = ref('')
    const plan = ref<PlanEventData | undefined>()
    const lastEventId = ref<string | undefined>()
    const lastTool = ref<ToolContent | undefined>()
    const lastNoMessageTool = ref<ToolContent | undefined>()

    const { handleEvent } = useAgentEvents(
      { messages, title, plan, lastEventId, lastTool, lastNoMessageTool },
    )

    handleEvent({
      event: 'plan',
      data: {
        event_id: 'p1',
        timestamp: Math.floor(Date.now() / 1000),
        steps: [
          { event_id: 'p1', timestamp: 1, id: '1', description: 'Research topic', status: 'running' },
          { event_id: 'p1', timestamp: 1, id: '2', description: 'Write report', status: 'pending' },
        ],
      },
    } as AgentEvent)

    expect(messages.value).toHaveLength(1)
    expect(messages.value[0].type).toBe('step')
    const step = messages.value[0].content as StepContent
    expect(step.id).toBe('1')
    expect(step.status).toBe('running')
  })

  it('follows file tools for the computer panel', () => {
    const messages = ref<Message[]>([])
    const title = ref('')
    const plan = ref<PlanEventData | undefined>()
    const lastEventId = ref<string | undefined>()
    const lastTool = ref<ToolContent | undefined>()
    const lastNoMessageTool = ref<ToolContent | undefined>()
    const activity: ToolContent[] = []

    const { handleEvent } = useAgentEvents(
      { messages, title, plan, lastEventId, lastTool, lastNoMessageTool },
      { onToolActivity: (t) => activity.push(t) },
    )

    handleEvent(makeToolEvent({ name: 'file', function: 'file_write', tool_call_id: 'file-1' }))

    expect(lastNoMessageTool.value?.tool_call_id).toBe('file-1')
    expect(activity).toHaveLength(1)
    expect(activity[0].function).toBe('file_write')
  })
})
