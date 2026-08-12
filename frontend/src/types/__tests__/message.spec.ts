import { describe, it, expect } from 'vitest'
import {
  shouldShowAssistantCopyActions,
  isStepConnectedToNext,
  resolveStepTimelineVisibility,
  type Message,
  type MessageContent,
  type StepContent,
  type ToolContent,
} from '../message'

function assistant(text: string): Message {
  return { type: 'assistant', content: { content: text, timestamp: 1 } as MessageContent }
}

function user(text: string): Message {
  return { type: 'user', content: { content: text, timestamp: 1 } as MessageContent }
}

describe('shouldShowAssistantCopyActions', () => {
  it('hides copy on last when footer owns it', () => {
    const messages = [user('q'), assistant('notify'), assistant('ask?')]
    expect(
      shouldShowAssistantCopyActions(messages, 2, 2, { footerOwnsLastCopy: true }),
    ).toBe(false)
  })

  it('hides copy on last while busy', () => {
    const messages = [user('q'), assistant('working…')]
    expect(
      shouldShowAssistantCopyActions(messages, 1, 1, { hideLastWhileBusy: true }),
    ).toBe(false)
  })

  it('shows copy on last when idle and no footer', () => {
    const messages = [user('q'), assistant('done')]
    expect(shouldShowAssistantCopyActions(messages, 1, 1)).toBe(true)
  })

  it('shows copy on earlier assistants even when footer owns last', () => {
    const messages = [user('q'), assistant('notify'), assistant('ask?')]
    expect(
      shouldShowAssistantCopyActions(messages, 1, 2, { footerOwnsLastCopy: true }),
    ).toBe(true)
  })

  it('hides copy on empty assistant text', () => {
    const messages = [assistant(''), assistant('hi')]
    expect(shouldShowAssistantCopyActions(messages, 0, 1)).toBe(false)
  })
})

function step(id: string): Message {
  return {
    type: 'step',
    content: {
      id,
      description: id,
      status: 'completed',
      tools: [],
      timestamp: 1,
    } as StepContent,
  }
}

describe('isStepConnectedToNext', () => {
  it('uses pb-0 only when the next message is also a step', () => {
    const messages = [user('q'), step('1'), step('2'), assistant('done')]
    expect(isStepConnectedToNext(messages, 1)).toBe(true)
    expect(isStepConnectedToNext(messages, 2)).toBe(false)
  })
})

function tool(id: string): ToolContent {
  return {
    tool_call_id: id,
    name: 'file',
    function: 'file_write',
    args: { file: `${id}.py` },
    status: 'called',
    timestamp: 1,
    brief: id,
  }
}

describe('resolveStepTimelineVisibility', () => {
  it('while running: collapsed shows only the last tool; preceding are expandable', () => {
    const stepContent: StepContent = {
      id: '1',
      description: 'Write code',
      status: 'running',
      tools: [tool('a'), tool('b'), tool('c')],
      timestamp: 1,
    }
    const v = resolveStepTimelineVisibility(stepContent)
    expect(v.precedingItems.map((i) => i.id)).toEqual(['a', 'b'])
    expect(v.lastToolItems.map((i) => i.id)).toEqual(['c'])
    expect(v.collapsedVisibleItems.map((i) => i.id)).toEqual(['c'])
    expect(v.canToggle).toBe(true)
  })

  it('when completed: collapsed hides tools; expand reveals all + result', () => {
    const stepContent: StepContent = {
      id: '1',
      description: 'Write code',
      status: 'completed',
      tools: [tool('a'), tool('b')],
      result: 'Done writing.',
      timestamp: 1,
    }
    const v = resolveStepTimelineVisibility(stepContent)
    expect(v.precedingItems.map((i) => i.id)).toEqual(['a', 'b'])
    expect(v.lastToolItems.map((i) => i.id)).toEqual(['result-1'])
    expect(v.collapsedVisibleItems).toEqual([])
    expect(v.canToggle).toBe(true)
  })

  it('single live tool cannot toggle (already visible while collapsed)', () => {
    const stepContent: StepContent = {
      id: '1',
      description: 'One tool',
      status: 'running',
      tools: [tool('only')],
      timestamp: 1,
    }
    const v = resolveStepTimelineVisibility(stepContent)
    expect(v.precedingItems).toEqual([])
    expect(v.collapsedVisibleItems.map((i) => i.id)).toEqual(['only'])
    expect(v.canToggle).toBe(false)
  })
})
