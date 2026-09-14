import { describe, it, expect } from 'vitest'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { SkillTag } from '../skillTag'
import { collectRequiredSkills } from '../requiredSkills'

describe('collectRequiredSkills', () => {
  it('collects skillTag attrs as id/name pairs', () => {
    const editor = new Editor({
      extensions: [StarterKit, SkillTag],
      content: {
        type: 'doc',
        content: [
          {
            type: 'paragraph',
            content: [
              {
                type: 'skillTag',
                attrs: { skillId: 'skill_slides', name: 'slides' },
              },
              { type: 'text', text: ' make a deck' },
            ],
          },
        ],
      },
    })

    expect(collectRequiredSkills(editor)).toEqual([
      { id: 'skill_slides', name: 'slides' },
    ])

    editor.destroy()
  })
})
