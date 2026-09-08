import type { Editor, JSONContent } from '@tiptap/core'

export type RequiredSkillRef = {
  id: string
  name: string
}

function walkNodes(node: JSONContent | undefined, visit: (node: JSONContent) => void) {
  if (!node) return
  visit(node)
  const content = node.content
  if (!content) return
  for (const child of content) {
    walkNodes(child, visit)
  }
}

/** Collect skillTag nodes for official-style requiredSkills payload. */
export function collectRequiredSkills(editor: Editor): RequiredSkillRef[] {
  const doc = editor.getJSON()
  const seen = new Set<string>()
  const out: RequiredSkillRef[] = []

  walkNodes(doc, (node) => {
    if (node.type !== 'skillTag') return
    const attrs = node.attrs as { skillId?: string; name?: string } | undefined
    const id = (attrs?.skillId || '').trim()
    const name = (attrs?.name || '').trim().replace(/^\//, '')
    if (!id || !name || seen.has(id)) return
    seen.add(id)
    out.push({ id, name })
  })

  return out
}
