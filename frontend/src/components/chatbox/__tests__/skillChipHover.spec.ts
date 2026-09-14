import { describe, it, expect, afterEach } from 'vitest'
import { bindSkillChipHover } from '../skillChipHover'
import { SKILL_CHIP_TOOLTIP_CLASS } from '../skillTag'

function makeChip(attrs: {
  id?: string
  name: string
  description?: string
  ownerType?: string
}): HTMLElement {
  const el = document.createElement('span')
  el.setAttribute('data-skill-tag', '')
  el.setAttribute('data-skill-name', `/${attrs.name}`)
  el.setAttribute('data-skill-id', attrs.id || '')
  el.setAttribute('data-skill-description', attrs.description || '')
  el.setAttribute('data-skill-owner', attrs.ownerType || '')
  el.textContent = attrs.name
  document.body.appendChild(el)
  return el
}

describe('bindSkillChipHover', () => {
  const cleanups: Array<() => void> = []

  afterEach(() => {
    while (cleanups.length) cleanups.pop()?.()
    document.querySelectorAll('[data-skill-tooltip]').forEach((n) => n.remove())
    document.querySelectorAll('[data-skill-tag]').forEach((n) => n.remove())
  })

  it('shows mined tooltip on mouseenter for chat-detail static chips', () => {
    const chip = makeChip({
      id: 'skill_summarize',
      name: 'summarize',
      description: 'Summarize long documents',
      ownerType: 'official',
    })
    cleanups.push(
      bindSkillChipHover(chip, () => ({
        skillId: chip.getAttribute('data-skill-id') || '',
        name: 'summarize',
        description: chip.getAttribute('data-skill-description') || '',
        ownerType: chip.getAttribute('data-skill-owner') || '',
      })),
    )

    chip.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }))
    const tip = document.querySelector('[data-skill-tooltip]') as HTMLElement | null
    expect(tip).toBeTruthy()
    expect(tip!.getAttribute('role')).toBe('tooltip')
    expect(tip!.className).toBe(SKILL_CHIP_TOOLTIP_CLASS)
    expect(tip!.textContent).toContain('summarize')
    expect(tip!.textContent).toContain('Summarize long documents')
    expect(tip!.textContent).toMatch(/Official|官方/)
  })

  it('hides tooltip on destroy cleanup', () => {
    const chip = makeChip({ name: 'slides', description: 'Make slides' })
    const unbind = bindSkillChipHover(chip, () => ({
      skillId: '',
      name: 'slides',
      description: 'Make slides',
      ownerType: '',
    }))
    chip.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }))
    expect(document.querySelector('[data-skill-tooltip]')).toBeTruthy()
    unbind()
    expect(document.querySelector('[data-skill-tooltip]')).toBeNull()
  })
})
