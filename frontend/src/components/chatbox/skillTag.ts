import { Node, mergeAttributes } from '@tiptap/core'
import { i18n } from '@/composables/useI18n'

export type SkillTagAttrs = {
  skillId: string
  name: string
  description?: string
  ownerType?: string
}

/** Mined from manus.im skill chip shell (excel-generator / typst-pdf-maker). */
export const SKILL_CHIP_SHELL_CLASS =
  'inline-flex max-w-[calc(100vw-48px)] sm:max-w-[400px] min-w-0 items-center gap-[6px] align-middle relative top-[-1px] rounded-[6px] border px-[6px] py-[2px] mx-[1px] transition-colors duration-150 border-[var(--border-dark)] hover:bg-[var(--fill-tsp-white-light)]'

/** Mined from manus.im skill-chip hover tooltip (`role="tooltip"`). */
export const SKILL_CHIP_TOOLTIP_CLASS =
  'w-max min-w-10 text-xs z-tooltip whitespace-pre-wrap break-words overflow-auto rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-card-gray)] text-[var(--text-secondary)] shadow-[0_4px_11px_0_var(--shadow-S)] backdrop-blur-[40px] p-0 max-w-none'

const SKILL_CHIP_ICON_WRAP_CLASS = 'flex shrink-0 items-center text-[var(--icon-tertiary)]'
const SKILL_CHIP_LABEL_CLASS = 'min-w-0 truncate text-sm text-[var(--text-secondary)]'
const TOOLTIP_BODY_CLASS = 'flex w-[248px] flex-col gap-2 p-4'
const TOOLTIP_TEXT_COL_CLASS = 'flex flex-col gap-[2px]'
const TOOLTIP_TITLE_CLASS =
  'truncate text-sm font-medium text-[var(--text-primary)] cursor-pointer hover:underline'
const TOOLTIP_DESC_CLASS = 'text-xs leading-4 text-[var(--text-tertiary)]'
const TOOLTIP_DESC_STYLE =
  'display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; word-break: break-word;'
const TOOLTIP_BADGE_ROW_CLASS = 'flex items-center gap-1'
const TOOLTIP_BADGE_CLASS =
  'inline-flex h-5 min-w-0 max-w-full items-center gap-1 rounded-[4px] bg-[var(--fill-tsp-white-main)] px-1 text-xs text-[var(--text-secondary)]'

const PUZZLE_PATH =
  'M15.39 4.39a1 1 0 0 0 1.68-.474 2.5 2.5 0 1 1 3.014 3.015 1 1 0 0 0-.474 1.68l1.683 1.682a2.414 2.414 0 0 1 0 3.414L19.61 15.39a1 1 0 0 1-1.68-.474 2.5 2.5 0 1 0-3.014 3.015 1 1 0 0 1 .474 1.68l-1.683 1.682a2.414 2.414 0 0 1-3.414 0L8.61 19.61a1 1 0 0 0-1.68.474 2.5 2.5 0 1 1-3.014-3.015 1 1 0 0 0 .474-1.68l-1.683-1.682a2.414 2.414 0 0 1 0-3.414L4.39 8.61a1 1 0 0 1 1.68.474 2.5 2.5 0 1 0 3.014-3.015 1 1 0 0 1-.474-1.68l1.683-1.682a2.414 2.414 0 0 1 3.414 0z'

/** Official badge shield (mined from excel-generator tooltip). */
const OFFICIAL_BADGE_SVG =
  '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="14" height="14" color="var(--icon-tertiary)" class="shrink-0"><path d="M12.6667 3.9997C11.1203 3.9997 9.31374 3.10864 8.07357 2.02639C8.05309 2.009 8.02688 1.9997 8 1.9997C7.97301 1.9997 7.94695 2.00951 7.92643 2.02704L7.92578 2.02639C6.69288 3.10132 4.88005 3.9997 3.33333 3.9997V8.66637C3.33333 10.1568 3.84707 11.2405 4.65755 12.0707C5.4863 12.9194 6.6557 13.5331 7.9974 13.9964C8.00225 13.9981 8.00756 13.9992 8.01237 14.001C9.34909 13.5345 10.5152 12.9207 11.3424 12.072C12.1526 11.2407 12.6667 10.1569 12.6667 8.66637V3.9997ZM9.52865 6.19501C9.78896 5.93486 10.211 5.93486 10.4714 6.19501C10.7317 6.45536 10.7317 6.87802 10.4714 7.13837L7.80469 9.80504C7.54438 10.0652 7.12228 10.0652 6.86198 9.80504L5.52865 8.47171C5.2683 8.21136 5.2683 7.7887 5.52865 7.52835C5.78896 7.2682 6.21104 7.2682 6.47135 7.52835L7.33333 8.39033L9.52865 6.19501ZM14 8.66637C14 10.5091 13.3473 11.9259 12.2975 13.003C11.2659 14.0614 9.88029 14.7628 8.44596 15.2627L8.44076 15.2647C8.15534 15.3614 7.84584 15.3579 7.5625 15.2562V15.2569C7.55858 15.2555 7.5547 15.2537 7.55078 15.2523C7.54976 15.2519 7.54855 15.252 7.54753 15.2517V15.251C6.11469 14.7547 4.73304 14.0565 3.70378 13.0023C2.65279 11.9259 2 10.509 2 8.66637V3.9997C2.00008 3.64619 2.14065 3.30697 2.39063 3.05699C2.64066 2.80704 2.97978 2.66637 3.33333 2.66637C4.45091 2.66637 5.96769 1.96748 7.05469 1.01793L7.06055 1.01337C7.32249 0.789588 7.65548 0.666367 8 0.666367C8.34452 0.666367 8.67751 0.789588 8.93945 1.01337L8.94531 1.01793C10.0383 1.97353 11.5486 2.66637 12.6667 2.66637C13.0202 2.66637 13.3593 2.80704 13.6094 3.05699C13.8594 3.30697 13.9999 3.64619 14 3.9997V8.66637Z" fill="currentColor"></path></svg>'

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

function buildTooltipDom(attrs: SkillTagAttrs): HTMLElement {
  const displayName = normalizeSkillName(attrs.name)
  const root = document.createElement('span')
  root.className = SKILL_CHIP_TOOLTIP_CLASS
  root.setAttribute('role', 'tooltip')
  root.setAttribute('tabindex', '-1')
  root.setAttribute('data-skill-tooltip', '')
  root.style.position = 'fixed'

  const body = document.createElement('div')
  body.className = TOOLTIP_BODY_CLASS

  const icon = document.createElement('div')
  icon.innerHTML = puzzleIconSvg(20, 'var(--icon-tertiary)')
  body.append(icon.firstElementChild as SVGElement)

  const textCol = document.createElement('div')
  textCol.className = TOOLTIP_TEXT_COL_CLASS

  const title = document.createElement('div')
  title.className = TOOLTIP_TITLE_CLASS
  title.textContent = displayName
  textCol.append(title)

  if (attrs.description) {
    const desc = document.createElement('div')
    desc.className = TOOLTIP_DESC_CLASS
    desc.setAttribute('style', TOOLTIP_DESC_STYLE)
    desc.textContent = attrs.description
    textCol.append(desc)
  }
  body.append(textCol)

  if (attrs.ownerType === 'official') {
    const row = document.createElement('div')
    row.className = TOOLTIP_BADGE_ROW_CLASS
    const badge = document.createElement('span')
    badge.className = TOOLTIP_BADGE_CLASS
    badge.innerHTML = OFFICIAL_BADGE_SVG
    const label = document.createElement('span')
    label.className = 'truncate'
    label.textContent = String(i18n.global.t('Official'))
    badge.append(label)
    row.append(badge)
    body.append(row)
  }

  root.append(body)
  return root
}

function positionTooltip(anchor: HTMLElement, tooltip: HTMLElement) {
  const gap = 7
  const pad = 8
  const rect = anchor.getBoundingClientRect()
  const tipRect = tooltip.getBoundingClientRect()
  const width = tipRect.width || 249
  const height = tipRect.height || 159
  let left = rect.left + rect.width / 2 - width / 2
  left = Math.min(Math.max(pad, left), window.innerWidth - width - pad)
  let top = rect.top - height - gap
  if (top < pad) {
    top = rect.bottom + gap
  }
  tooltip.style.left = `${Math.round(left)}px`
  tooltip.style.top = `${Math.round(top)}px`
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
      let tooltip: HTMLElement | null = null
      let hideTimer: number | null = null

      const clearHide = () => {
        if (hideTimer != null) {
          window.clearTimeout(hideTimer)
          hideTimer = null
        }
      }

      const hideNow = () => {
        clearHide()
        tooltip?.remove()
        tooltip = null
      }

      const show = () => {
        clearHide()
        if (!tooltip) {
          tooltip = buildTooltipDom(current)
          tooltip.addEventListener('mouseenter', show)
          tooltip.addEventListener('mouseleave', scheduleHide)
          document.body.appendChild(tooltip)
        }
        positionTooltip(dom, tooltip)
      }

      const scheduleHide = () => {
        clearHide()
        hideTimer = window.setTimeout(hideNow, 100)
      }

      dom.addEventListener('mouseenter', show)
      dom.addEventListener('mouseleave', scheduleHide)

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
          if (tooltip) {
            const nextTip = buildTooltipDom(current)
            tooltip.replaceWith(nextTip)
            tooltip = nextTip
            tooltip.addEventListener('mouseenter', show)
            tooltip.addEventListener('mouseleave', scheduleHide)
            positionTooltip(dom, tooltip)
          }
          return true
        },
        destroy() {
          dom.removeEventListener('mouseenter', show)
          dom.removeEventListener('mouseleave', scheduleHide)
          hideNow()
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
