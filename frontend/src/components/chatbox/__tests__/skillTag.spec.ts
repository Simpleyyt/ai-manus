import { describe, it, expect } from 'vitest'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { SkillTag, SKILL_CHIP_SHELL_CLASS, SKILL_CHIP_TOOLTIP_CLASS } from '../skillTag'

function makeEditor() {
  return new Editor({
    extensions: [StarterKit, SkillTag],
    content: { type: 'doc', content: [{ type: 'paragraph' }] },
  })
}

describe('SkillTag', () => {
  it('serializes to /{name} in getText', () => {
    const editor = makeEditor()
    editor.commands.setContent({
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'skillTag',
              attrs: { skillId: 'skill_slides', name: 'slides' },
            },
            { type: 'text', text: ' please' },
          ],
        },
      ],
    })
    expect(editor.getText()).toBe('/slides please')
    editor.destroy()
  })

  it('renders official-style bordered chip without leading slash in label', () => {
    const editor = makeEditor()
    editor.commands.insertContent({
      type: 'skillTag',
      attrs: { skillId: 'skill_slides', name: 'slides' },
    })
    const el = editor.view.dom.querySelector('[data-skill-tag]') as HTMLElement | null
    expect(el).toBeTruthy()
    expect(el!.getAttribute('data-skill-name')).toBe('/slides')
    expect(el!.getAttribute('data-skill-id')).toBe('skill_slides')
    expect(el!.textContent).toBe('slides')

    const shell = el!.querySelector(`.${SKILL_CHIP_SHELL_CLASS.split(' ')[0]}`) as HTMLElement | null
    // Match full mined class string on the chip shell
    const chip = el!.querySelector('span.inline-flex') as HTMLElement | null
    expect(chip).toBeTruthy()
    expect(chip!.className).toBe(SKILL_CHIP_SHELL_CLASS)
    expect(el!.querySelector('svg.lucide')).toBeTruthy()
    expect(shell || chip).toBeTruthy()
    editor.destroy()
  })

  it('shows mined hover tooltip with description and official badge', () => {
    const editor = makeEditor()
    editor.commands.insertContent({
      type: 'skillTag',
      attrs: {
        skillId: 'skill_slides',
        name: 'slides',
        description: 'Turn an outline into presentation slides',
        ownerType: 'official',
      },
    })
    const el = editor.view.dom.querySelector('[data-skill-tag]') as HTMLElement
    el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }))
    const tip = document.querySelector('[data-skill-tooltip]') as HTMLElement | null
    expect(tip).toBeTruthy()
    expect(tip!.getAttribute('role')).toBe('tooltip')
    expect(tip!.className).toBe(SKILL_CHIP_TOOLTIP_CLASS)
    expect(tip!.textContent).toContain('slides')
    expect(tip!.textContent).toContain('Turn an outline into presentation slides')
    expect(tip!.textContent).toMatch(/Official|官方/)
    editor.destroy()
    expect(document.querySelector('[data-skill-tooltip]')).toBeNull()
  })
})
