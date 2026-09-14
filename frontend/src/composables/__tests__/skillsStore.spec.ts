import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  addSkills,
  filterSkillsByQuery,
  isSkillAdded,
  isSkillEnabled,
  resetSkillsStoreForTests,
  setSkillsStoreForTests,
  setSkillEnabled,
} from '../skillsStore'
import type { AddedSkill } from '@/api/skills'

vi.mock('@/api/skills', () => ({
  fetchSkillsState: vi.fn(),
  addSkills: vi.fn(),
  setSkillEnabled: vi.fn(),
  importSkillFromGitHub: vi.fn(),
  importSkillFromUpload: vi.fn(),
}))

const sampleAdded: AddedSkill[] = [
  {
    id: 'skill_market_research',
    name: 'market-research',
    description: 'Research markets',
    owner_type: 'official',
    enabled: true,
  },
  {
    id: 'skill_slides',
    name: 'slides',
    description: 'Slides',
    owner_type: 'official',
    enabled: false,
  },
]

describe('skillsStore', () => {
  beforeEach(() => {
    resetSkillsStoreForTests()
    setSkillsStoreForTests({
      catalog: sampleAdded,
      added: sampleAdded,
    })
  })

  it('filters added skills by query', () => {
    expect(filterSkillsByQuery('market').map((s) => s.id)).toEqual(['skill_market_research'])
  })

  it('tracks added and enabled state', () => {
    expect(isSkillAdded('skill_market_research')).toBe(true)
    expect(isSkillEnabled('skill_slides')).toBe(false)
  })

  it('delegates setSkillEnabled to API', async () => {
    const api = await import('@/api/skills')
    vi.mocked(api.setSkillEnabled).mockResolvedValue({
      ...sampleAdded[1],
      enabled: true,
    })
    await setSkillEnabled('skill_slides', true)
    expect(api.setSkillEnabled).toHaveBeenCalledWith('skill_slides', true)
    expect(isSkillEnabled('skill_slides')).toBe(true)
  })

  it('delegates addSkills to API and refreshes store', async () => {
    const api = await import('@/api/skills')
    vi.mocked(api.addSkills).mockResolvedValue({
      catalog: sampleAdded,
      added: [
        ...sampleAdded,
        {
          id: 'skill_web_research',
          name: 'web-research',
          description: 'Web research',
          owner_type: 'official',
          enabled: true,
        },
      ],
    })
    await addSkills(['skill_web_research'])
    expect(isSkillAdded('skill_web_research')).toBe(true)
  })

  it('launchSkillCreatorFlow adds skill_creator and returns it', async () => {
    const api = await import('@/api/skills')
    const creator = {
      id: 'skill_creator',
      name: 'skill-creator',
      description: 'Build a reusable skill together with Manus',
      owner_type: 'official' as const,
      enabled: true,
    }
    vi.mocked(api.addSkills).mockResolvedValue({
      catalog: [...sampleAdded, creator],
      added: [...sampleAdded, creator],
    })
    const { launchSkillCreatorFlow } = await import('../skillsStore')
    const skill = await launchSkillCreatorFlow()
    expect(api.addSkills).toHaveBeenCalledWith(['skill_creator'])
    expect(skill.id).toBe('skill_creator')
    expect(skill.name).toBe('skill-creator')
  })
})
