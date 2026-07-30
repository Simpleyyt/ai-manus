import { Extension, type Editor, type Range } from '@tiptap/core'
import Suggestion, {
  type SuggestionKeyDownProps,
  type SuggestionProps,
} from '@tiptap/suggestion'

export type SlashItem = {
  id: 'add_local_files'
  titleKey: string
  run: () => void
}

export function buildSlashItems(runAddLocalFiles: () => void): SlashItem[] {
  return [
    {
      id: 'add_local_files',
      titleKey: 'Add local files',
      run: runAddLocalFiles,
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
            return opts.items().filter(
              (item) =>
                q === '' ||
                item.id.includes(q) ||
                item.titleKey.toLowerCase().includes(q),
            )
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
