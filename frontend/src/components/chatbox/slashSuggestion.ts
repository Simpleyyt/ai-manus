import { Extension, type Editor, type Range } from '@tiptap/core'
import Suggestion, {
  type SuggestionKeyDownProps,
  type SuggestionProps,
} from '@tiptap/suggestion'
import type { Skill } from '@/types/skill'

export type SlashItem =
  | {
      id: 'add_local_files'
      kind: 'local'
      titleKey: string
      run: () => void
    }
  | {
      id: string
      kind: 'skill'
      titleKey: string
      skillId: string
      name: string
      description: string
      run: () => void
    }

export function buildSlashItems(opts: {
  runAddLocalFiles: () => void
  skills: Skill[]
  onInsertSkill: (skill: Skill) => void
}): SlashItem[] {
  const skillItems: SlashItem[] = opts.skills.map((skill) => ({
    id: skill.id,
    kind: 'skill',
    titleKey: skill.name,
    skillId: skill.id,
    name: skill.name,
    description: skill.description,
    run: () => opts.onInsertSkill(skill),
  }))

  return [
    ...skillItems,
    {
      id: 'add_local_files',
      kind: 'local',
      titleKey: 'Add local files',
      run: opts.runAddLocalFiles,
    },
  ]
}

/**
 * Prefer the TipTap suggestion `command` (deletes `/` query + runs item).
 * When mouse blur clears `command` before click, fall back to stored `range`.
 */
export function applySlashSelection(opts: {
  editor: Editor | null | undefined
  range: Range | null
  command: ((item: SlashItem) => void) | null
  item: SlashItem
}): void {
  if (opts.command) {
    opts.command(opts.item)
    return
  }
  if (opts.editor && opts.range) {
    opts.editor.chain().focus().deleteRange(opts.range).run()
  }
  opts.item.run()
}

export type SlashSuggestionRenderHandlers = {
  onStart: (props: SuggestionProps<SlashItem>) => void
  onUpdate: (props: SuggestionProps<SlashItem>) => void
  onExit: () => void
  onKeyDown: (props: SuggestionKeyDownProps) => boolean
}

export function createSlashSuggestion(opts: {
  items: () => SlashItem[]
  onOpenChange?: (open: boolean) => void
  render?: SlashSuggestionRenderHandlers
}): Extension {
  return Extension.create({
    name: 'slashSuggestion',
    addProseMirrorPlugins() {
      return [
        Suggestion<SlashItem>({
          editor: this.editor,
          char: '/',
          allowSpaces: false,
          items: ({ query }) => {
            const q = query.toLowerCase()
            return opts.items().filter((item) => {
              if (q === '') return true
              if (item.kind === 'local') {
                return item.id.includes(q) || item.titleKey.toLowerCase().includes(q)
              }
              return (
                item.name.toLowerCase().includes(q) ||
                item.description.toLowerCase().includes(q)
              )
            })
          },
          command: ({ editor, range, props }) => {
            editor.chain().focus().deleteRange(range).run()
            props.run()
          },
          render: () => ({
            onStart: (props) => {
              opts.onOpenChange?.(true)
              opts.render?.onStart(props)
            },
            onUpdate: (props) => {
              opts.render?.onUpdate(props)
            },
            onExit: () => {
              opts.onOpenChange?.(false)
              opts.render?.onExit()
            },
            onKeyDown: (props) => opts.render?.onKeyDown(props) ?? false,
          }),
        }),
      ]
    },
  })
}
