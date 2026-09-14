import { describe, it, expect } from 'vitest'
import {
  renderSkillChipHtml,
  splitLeadingSkillChips,
  formatUserMessageWithSkillChips,
} from '../skillChipHtml'
import { SKILL_CHIP_SHELL_CLASS } from '../skillTag'

describe('skillChipHtml', () => {
  it('renders bordered chip html with puzzle icon and no leading slash', () => {
    const html = renderSkillChipHtml({
      id: 'skill_summarize',
      name: 'summarize',
      description: 'Summarize long documents',
      ownerType: 'official',
    })
    expect(html).toContain('data-skill-tag')
    expect(html).toContain('data-skill-name="/summarize"')
    expect(html).toContain('data-skill-description="Summarize long documents"')
    expect(html).toContain('data-skill-owner="official"')
    expect(html).toContain(SKILL_CHIP_SHELL_CLASS)
    expect(html).toContain('>summarize<')
    expect(html).not.toContain('>/summarize<')
    expect(html).toContain('<svg')
  })

  it('splits leading /name tokens using required_skills', () => {
    const split = splitLeadingSkillChips(
      '/summarize 请总结远程办公',
      [{ id: 'skill_summarize', name: 'summarize' }],
    )
    expect(split.skills).toEqual([
      { id: 'skill_summarize', name: 'summarize', description: '', ownerType: '' },
    ])
    expect(split.body).toBe('请总结远程办公')
  })

  it('falls back to slash token when required_skills missing', () => {
    const split = splitLeadingSkillChips('/slides make a deck', [])
    expect(split.skills).toEqual([{ id: '', name: 'slides' }])
    expect(split.body).toBe('make a deck')
  })

  it('formats bubble html with chip then body text', () => {
    const html = formatUserMessageWithSkillChips(
      '/summarize hello',
      [{ id: 'skill_summarize', name: 'summarize' }],
    )
    expect(html).toContain('data-skill-tag')
    expect(html).toContain('<svg')
    expect(html).toContain(SKILL_CHIP_SHELL_CLASS)
    expect(html).toContain('hello')
    expect(html).not.toContain('/summarize hello')
  })
})
