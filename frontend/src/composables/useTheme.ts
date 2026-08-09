export type ThemeMode = 'light' | 'dark' | 'auto'

const THEME_STORAGE_KEY = 'manus-theme-mode'

let mediaQuery: MediaQueryList | null = null
let mediaHandler: ((e: MediaQueryListEvent) => void) | null = null

function systemPrefersDark(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function applyThemeMode(mode: ThemeMode): void {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  const dark = mode === 'dark' || (mode === 'auto' && systemPrefersDark())
  root.classList.toggle('dark', dark)
}

function detachMediaListener(): void {
  if (mediaQuery && mediaHandler) {
    mediaQuery.removeEventListener('change', mediaHandler)
  }
  mediaQuery = null
  mediaHandler = null
}

function attachAutoListener(): void {
  detachMediaListener()
  if (typeof window === 'undefined' || !window.matchMedia) return
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaHandler = () => applyThemeMode('auto')
  mediaQuery.addEventListener('change', mediaHandler)
}

export function readStoredThemeMode(): ThemeMode {
  try {
    const raw = localStorage.getItem(THEME_STORAGE_KEY)
    if (raw === 'light' || raw === 'dark' || raw === 'auto') return raw
  } catch {
    /* ignore */
  }
  return 'auto'
}

export function setThemeMode(mode: ThemeMode): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode)
  } catch {
    /* ignore */
  }
  if (mode === 'auto') {
    attachAutoListener()
  } else {
    detachMediaListener()
  }
  applyThemeMode(mode)
}

export function initTheme(): ThemeMode {
  const mode = readStoredThemeMode()
  setThemeMode(mode)
  return mode
}

/** Current resolved dark state (after `dark` class is applied). */
export function isDocumentDark(): boolean {
  if (typeof document === 'undefined') return false
  return (
    document.documentElement.classList.contains('dark')
    || document.body.classList.contains('dark')
  )
}
