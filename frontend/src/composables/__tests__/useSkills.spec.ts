import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setSkillsStoreForTests, resetSkillsStoreForTests } from '../skillsStore'
import { useSkills } from '../useSkills'

vi.mock('@/api/skills', () => ({
  fetchSkillsState: vi.fn(),
  addSkills: vi.fn(),
  setSkillEnabled: vi.fn(),
  importSkillFromGitHub: vi.fn(),
  importSkillFromUpload: vi.fn(),
}))

describe('useSkills', () => {
  beforeEach(() => {
    resetSkillsStoreForTests()
    setSkillsStoreForTests({
      added: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
          enabled: true,
        },
      ],
      catalog: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
        },
      ],
    })
  })

  it('exposes added skills from store', () => {
    const { skills } = useSkills()
    expect(skills.value).toHaveLength(1)
    expect(skills.value[0].name).toBe('market-research')
  })

  it('filterByQuery matches name case-insensitively', () => {
    const { filterByQuery } = useSkills()
    expect(filterByQuery('MARKET')).toHaveLength(1)
    expect(filterByQuery('___no_such_skill___')).toEqual([])
  })
})
