import { describe, it, expect, beforeEach } from 'vitest'
import {
  setPendingHomeDraft,
  consumePendingHomeDraft,
  pendingHomeDraft,
  setPendingHomeMessage,
  consumePendingHomeMessage,
} from '../usePendingHomeMessage'

describe('usePendingHomeMessage', () => {
  beforeEach(() => {
    pendingHomeDraft.value = null
  })

  it('stores and consumes a skill-creator style draft once', () => {
    setPendingHomeDraft({
      before: 'Help me create a skill together using ',
      skill: {
        skillId: 'skill_creator',
        name: 'skill-creator',
        description: 'Build a skill',
        ownerType: 'official',
      },
      after: ' to create a skill. First ask me what the skill should do.',
    })
    expect(pendingHomeDraft.value?.skill.name).toBe('skill-creator')
    const draft = consumePendingHomeDraft()
    expect(draft?.skill.skillId).toBe('skill_creator')
    expect(consumePendingHomeDraft()).toBeNull()
  })

  it('legacy plain message helpers still round-trip', () => {
    setPendingHomeMessage('hello draft')
    expect(consumePendingHomeMessage()).toBe('hello draft')
  })
})
