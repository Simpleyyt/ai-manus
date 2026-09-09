import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  SKILL_CHIP_SHELL_CLASS,
} from './skillTag'

export type SkillChipRef = {
  id: string
  name: string
  description?: string
  ownerType?: string
}

const PUZZLE_PATH =
  'M15.39 4.39a1 1 0 0 0 1.68-.474 2.5 2.5 0 1 1 3.014 3.015 1 1 0 0 0-.474 1.68l1.683 1.682a2.414 2.414 0 0 1 0 3.414L19.61 15.39a1 1 0 0 1-1.68-.474 2.5 2.5 0 1 0-3.014 3.015 1 1 0 0 1 .474 1.68l-1.683 1.682a2.414 2.414 0 0 1-3.414 0L8.61 19.61a1 1 0 0 0-1.68.474 2.5 2.5 0 1 1-3.014-3.015 1 1 0 0 0 .474-1.68l-1.683-1.682a2.414 2.414 0 0 1 0-3.414L4.39 8.61a1 1 0 0 1 1.68.474 2.5 2.5 0 1 0 3.014-3.015 1 1 0 0 1-.474-1.68l1.683-1.682a2.414 2.414 0 0 1 3.414 0z'

const SKILL_CHIP_ICON_WRAP_CLASS = 'flex shrink-0 items-center text-[var(--icon-tertiary)]'
const SKILL_CHIP_LABEL_CLASS = 'min-w-0 truncate text-sm text-[var(--text-secondary)]'

function normalizeSkillName(name: string): string {
  return String(name || '')
    .trim()
    .replace(/^\//, '')
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** Same bordered chip shell as TipTap SkillTag (composer). */
export function renderSkillChipHtml(skill: SkillChipRef): string {
  const name = normalizeSkillName(skill.name)
  const id = escapeHtml(skill.id || '')
  const safeName = escapeHtml(name)
  const description = escapeHtml(skill.description || '')
  const ownerType = escapeHtml(skill.ownerType || '')
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" ` +
    `stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ` +
    `class="lucide" aria-hidden="true"><path d="${PUZZLE_PATH}"></path></svg>`
  return (
    `<span data-skill-tag data-skill-name="/${safeName}" data-skill-id="${id}" ` +
    `data-skill-description="${description}" data-skill-owner="${ownerType}" ` +
    `contenteditable="false" draggable="false" tabindex="0" style="white-space: normal;">` +
    `<span class="${SKILL_CHIP_SHELL_CLASS}">` +
    `<span class="${SKILL_CHIP_ICON_WRAP_CLASS}">${svg}</span>` +
    `<span class="${SKILL_CHIP_LABEL_CLASS}">${safeName}</span>` +
    `</span></span>`
  )
}

/**
 * Peel leading `/{name}` tokens (from getText / persisted user message) into
 * skill chip refs, leaving the remaining body for markdown.
 */
export function splitLeadingSkillChips(
  text: string,
  requiredSkills: SkillChipRef[] = [],
): { skills: SkillChipRef[]; body: string } {
  let rest = String(text || '')
  const skills: SkillChipRef[] = []
  const used = new Set<string>()

  const tryConsume = (skill: SkillChipRef): boolean => {
    const name = normalizeSkillName(skill.name)
    if (!name || used.has(name.toLowerCase())) return false
    const re = new RegExp(`^\\s*/${escapeRegExp(name)}(?=\\s|$)`, 'i')
    if (!re.test(rest)) return false
    rest = rest.replace(re, '')
    skills.push({
      id: skill.id || '',
      name,
      description: skill.description || '',
      ownerType: skill.ownerType || '',
    })
    used.add(name.toLowerCase())
    return true
  }

  let progressed = true
  while (progressed) {
    progressed = false
    for (const skill of requiredSkills) {
      if (tryConsume(skill)) {
        progressed = true
        break
      }
    }
  }

  // History without required_skills: still chip the leading /token.
  if (!skills.length) {
    const m = rest.match(/^\s*\/([a-z0-9][a-z0-9_-]*)(?=\s|$)/i)
    if (m) {
      skills.push({ id: '', name: m[1] })
      rest = rest.slice(m[0].length)
    }
  }

  return { skills, body: rest.replace(/^\s+/, '') }
}

const inlineRenderer = new marked.Renderer()
inlineRenderer.link = ({ href, title, text }: { href: string; title?: string | null; text: string }) => {
  const titleAttr = title ? ` title="${title}"` : ''
  return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`
}

/** Chat-detail bubble HTML: official skill chips + remaining markdown body. */
export function formatUserMessageWithSkillChips(
  text: string,
  requiredSkills: SkillChipRef[] = [],
): string {
  const { skills, body } = splitLeadingSkillChips(text, requiredSkills)
  const chips = skills.map((s) => renderSkillChipHtml(s)).join('')
  const bodyHtml = body
    ? (marked.parseInline(body, { renderer: inlineRenderer }) as string)
    : ''
  const joined = chips && bodyHtml ? `${chips} ${bodyHtml}` : `${chips}${bodyHtml}`
  return DOMPurify.sanitize(joined, {
    ADD_ATTR: [
      'target',
      'data-skill-tag',
      'data-skill-name',
      'data-skill-id',
      'data-skill-description',
      'data-skill-owner',
      'contenteditable',
      'draggable',
      'tabindex',
      'stroke',
      'stroke-width',
      'stroke-linecap',
      'stroke-linejoin',
      'aria-hidden',
      'viewBox',
      'fill',
      'xmlns',
    ],
    ADD_TAGS: ['svg', 'path'],
  })
}
