import { Node, mergeAttributes } from '@tiptap/core'
import {
  bindSkillChipHover,
  type SkillTagAttrs,
} from './skillChipHover'

export type { SkillTagAttrs }
export { SKILL_CHIP_TOOLTIP_CLASS } from './skillChipHover'

/** Mined from manus.im skill chip shell (excel-generator / typst-pdf-maker). */
export const SKILL_CHIP_SHELL_CLASS =
  'inline-flex max-w-[calc(100vw-48px)] sm:max-w-[400px] min-w-0 items-center gap-[6px] align-middle relative top-[-1px] rounded-[6px] border px-[6px] py-[2px] mx-[1px] transition-colors duration-150 border-[var(--border-dark)] hover:bg-[var(--fill-tsp-white-light)]'

const SKILL_CHIP_ICON_WRAP_CLASS = 'flex shrink-0 items-center text-[var(--icon-tertiary)]'
const SKILL_CHIP_LABEL_CLASS = 'min-w-0 truncate text-sm text-[var(--text-secondary)]'

const PUZZLE_PATH =
  'M15.39 4.39a1 1 0 0 0 1.68-.474 2.5 2.5 0 1 1 3.014 3.015 1 1 0 0 0-.474 1.68l1.683 1.682a2.414 2.414 0 0 1 0 3.414L19.61 15.39a1 1 0 0 1-1.68-.474 2.5 2.5 0 1 0-3.014 3.015 1 1 0 0 1 .474 1.68l-1.683 1.682a2.414 2.414 0 0 1-3.414 0L8.61 19.61a1 1 0 0 0-1.68.474 2.5 2.5 0 1 1-3.014-3.015 1 1 0 0 0 .474-1.68l-1.683-1.682a2.414 2.414 0 0 1 0-3.414L4.39 8.61a1 1 0 0 1 1.68.474 2.5 2.5 0 1 0 3.014-3.015 1 1 0 0 1-.474-1.68l1.683-1.682a2.414 2.414 0 0 1 3.414 0z'

function puzzleIconSvg(size: number, stroke: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide" aria-hidden="true"><path d="${PUZZLE_PATH}"></path></svg>`
}

function normalizeSkillName(name: unknown): string {
  return String(name || '')
    .trim()
    .replace(/^\//, '')
}

function attrsFromNode(node: { attrs: Record<string, unknown> }): SkillTagAttrs {
  return {
    skillId: String(node.attrs.skillId || ''),
    name: normalizeSkillName(node.attrs.name),
    description: String(node.attrs.description || ''),
    ownerType: String(node.attrs.ownerType || ''),
  }
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    skillTag: {
      insertSkillTag: (attrs: SkillTagAttrs) => ReturnType
    }
  }
}

function buildChipDom(attrs: SkillTagAttrs): HTMLElement {
  const displayName = normalizeSkillName(attrs.name)
  const root = document.createElement('span')
  root.setAttribute('data-skill-tag', '')
  root.setAttribute('data-skill-name', `/${displayName}`)
  root.setAttribute('data-skill-id', attrs.skillId || '')
  root.setAttribute('data-skill-description', attrs.description || '')
  root.setAttribute('data-skill-owner', attrs.ownerType || '')
  root.setAttribute('contenteditable', 'false')
  root.setAttribute('draggable', 'false')
  root.setAttribute('tabindex', '0')
  root.style.whiteSpace = 'normal'

  const shell = document.createElement('span')
  shell.className = SKILL_CHIP_SHELL_CLASS

  const iconWrap = document.createElement('span')
  iconWrap.className = SKILL_CHIP_ICON_WRAP_CLASS
  iconWrap.innerHTML = puzzleIconSvg(14, 'currentColor')

  const label = document.createElement('span')
  label.className = SKILL_CHIP_LABEL_CLASS
  label.textContent = displayName

  shell.append(iconWrap, label)
  root.append(shell)
  return root
}

export const SkillTag = Node.create({
  name: 'skillTag',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  draggable: false,

  addAttributes() {
    return {
      skillId: { default: '' },
      name: { default: '' },
      description: { default: '' },
      ownerType: { default: '' },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-skill-tag]',
        getAttrs: (el) => {
          if (!(el instanceof HTMLElement)) return false
          return {
            skillId: el.getAttribute('data-skill-id') || '',
            name: normalizeSkillName(el.getAttribute('data-skill-name') || ''),
            description: el.getAttribute('data-skill-description') || '',
            ownerType: el.getAttribute('data-skill-owner') || '',
          }
        },
      },
      {
        tag: 'span[data-skill-name]',
        getAttrs: (el) => {
          if (!(el instanceof HTMLElement)) return false
          return {
            skillId: el.getAttribute('data-skill-id') || '',
            name: normalizeSkillName(el.getAttribute('data-skill-name') || ''),
            description: el.getAttribute('data-skill-description') || '',
            ownerType: el.getAttribute('data-skill-owner') || '',
          }
        },
      },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    const displayName = normalizeSkillName(node.attrs.name)
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-skill-tag': '',
        'data-skill-name': `/${displayName}`,
        'data-skill-id': node.attrs.skillId,
        'data-skill-description': node.attrs.description || '',
        'data-skill-owner': node.attrs.ownerType || '',
        contenteditable: 'false',
        draggable: 'false',
        tabindex: '0',
        style: 'white-space: normal;',
      }),
      [
        'span',
        { class: SKILL_CHIP_SHELL_CLASS },
        ['span', { class: SKILL_CHIP_ICON_WRAP_CLASS }],
        ['span', { class: SKILL_CHIP_LABEL_CLASS }, displayName],
      ],
    ]
  },

  addNodeView() {
    return ({ node }) => {
      let current = attrsFromNode(node)
      const dom = buildChipDom(current)
      let unbind = bindSkillChipHover(dom, () => current)

      return {
        dom,
        update(updated) {
          if (updated.type.name !== 'skillTag') return false
          current = attrsFromNode(updated)
          const next = buildChipDom(current)
          dom.replaceChildren(...Array.from(next.childNodes))
          for (const name of [
            'data-skill-name',
            'data-skill-id',
            'data-skill-description',
            'data-skill-owner',
          ] as const) {
            dom.setAttribute(name, next.getAttribute(name) || '')
          }
          // Rebind so an open tooltip picks up refreshed attrs.
          unbind()
          unbind = bindSkillChipHover(dom, () => current)
          return true
        },
        destroy() {
          unbind()
        },
      }
    }
  },

  renderText({ node }) {
    return `/${normalizeSkillName(node.attrs.name)}`
  },

  addCommands() {
    return {
      insertSkillTag:
        (attrs) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs: {
              skillId: attrs.skillId,
              name: normalizeSkillName(attrs.name),
              description: attrs.description || '',
              ownerType: attrs.ownerType || '',
            },
          }),
    }
  },
})
