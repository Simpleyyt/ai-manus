/**
 * Lightweight syntax coloring for Library card previews (no shiki dependency).
 * Escapes HTML then wraps keywords / strings / comments / numbers.
 */
export function highlightLibraryPreview(source: string, ext: string): string {
  const escaped = source
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const parts: string[] = [];
  const stash = (html: string) => {
    const id = parts.length;
    parts.push(html);
    // Letter-only marker so later \b\d+\b won't eat the index
    return `«${'a'.repeat(id + 1)}»`;
  };

  let s = escaped;

  // Comments
  s = s.replace(/\/\*[\s\S]*?\*\//g, (m) => stash(`<span class="tok-cmt">${m}</span>`));
  s = s.replace(/\/\/[^\n]*/g, (m) => stash(`<span class="tok-cmt">${m}</span>`));
  if (['py', 'sh', 'bash', 'yaml', 'yml', 'rb'].includes(ext)) {
    s = s.replace(/#[^\n]*/g, (m) => stash(`<span class="tok-cmt">${m}</span>`));
  }

  // Strings
  s = s.replace(
    /('''[\s\S]*?'''|"""[\s\S]*?"""|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")/g,
    (m) => stash(`<span class="tok-str">${m}</span>`),
  );

  const keywords = KEYWORDS[ext] || KEYWORDS.default;
  const kwRe = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
  s = s.replace(kwRe, '<span class="tok-kw">$1</span>');
  s = s.replace(/\b(\d+\.?\d*)\b/g, '<span class="tok-num">$1</span>');

  s = s.replace(/«(a+)»/g, (_, a: string) => parts[a.length - 1]);
  return s;
}

const KEYWORDS: Record<string, string[]> = {
  py: [
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
    'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
    'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
    'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
    'self', 'print',
  ],
  js: [
    'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
    'default', 'delete', 'do', 'else', 'export', 'extends', 'false', 'finally',
    'for', 'function', 'if', 'import', 'in', 'instanceof', 'let', 'new', 'null',
    'return', 'static', 'super', 'switch', 'this', 'throw', 'true', 'try',
    'typeof', 'var', 'void', 'while', 'with', 'yield', 'async', 'of',
  ],
  ts: [],
  jsx: [],
  tsx: [],
  vue: [],
  java: [
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
    'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
    'extends', 'final', 'finally', 'float', 'for', 'if', 'implements', 'import',
    'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package',
    'private', 'protected', 'public', 'return', 'short', 'static', 'super',
    'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try',
    'void', 'volatile', 'while', 'true', 'false', 'null',
  ],
  go: [
    'break', 'case', 'chan', 'const', 'continue', 'default', 'defer', 'else',
    'fallthrough', 'for', 'func', 'go', 'goto', 'if', 'import', 'interface',
    'map', 'package', 'range', 'return', 'select', 'struct', 'switch', 'type',
    'var', 'true', 'false', 'nil',
  ],
  default: [
    'class', 'def', 'function', 'return', 'if', 'else', 'for', 'while', 'import',
    'from', 'const', 'let', 'var', 'true', 'false', 'null', 'None', 'True', 'False',
  ],
};

KEYWORDS.ts = KEYWORDS.js;
KEYWORDS.jsx = KEYWORDS.js;
KEYWORDS.tsx = KEYWORDS.js;
KEYWORDS.vue = KEYWORDS.js;
