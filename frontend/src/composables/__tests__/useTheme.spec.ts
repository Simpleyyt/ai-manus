import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  applyThemeMode,
  readStoredThemeMode,
  setThemeMode,
  initTheme,
} from '../useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: query.includes('dark'),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
      onchange: null,
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    document.documentElement.classList.remove('dark')
    localStorage.clear()
  })

  it('defaults stored mode to auto', () => {
    expect(readStoredThemeMode()).toBe('auto')
  })

  it('applyThemeMode light removes dark class', () => {
    document.documentElement.classList.add('dark')
    applyThemeMode('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applyThemeMode dark adds dark class', () => {
    applyThemeMode('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('setThemeMode persists and applies', () => {
    setThemeMode('dark')
    expect(localStorage.getItem('manus-theme-mode')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('initTheme restores stored preference', () => {
    localStorage.setItem('manus-theme-mode', 'light')
    expect(initTheme()).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
