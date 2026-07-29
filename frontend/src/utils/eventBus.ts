import mitt from 'mitt'
import type { FileInfo } from '../api/file'

/** UI mutual-exclusion / panel chrome */
export const UI_SHOW_FILE_PREVIEWER = 'ui:show-file-previewer' as const
export const UI_SHOW_COMPUTER_PANEL = 'ui:show-computer-panel' as const

/**
 * Typed app-wide mitt bus. No `[key: string]` escape — new events must be declared here.
 */
export type AppEvents = {
  'projects:changed': undefined
  'sessions:changed': undefined
  'ui:show-file-previewer': undefined
  'ui:show-computer-panel': undefined
  /** VNC browser takeover overlay */
  'ui:takeover': {
    sessionId: string
    active: boolean
  }
  /** Global toast notifications */
  'ui:toast': {
    message: string
    type: 'error' | 'info' | 'success'
    duration: number
  }
  /** Token refresh failed — clear session silently */
  'auth:logout': undefined
  /** Official terminalUpdate — live shell console */
  'tool:terminal_update': {
    sessionId: string
    shellId: string
    output: unknown
  }
  /** Official file / text_editor panel update */
  'tool:file_update': {
    sessionId: string
    path: string
    content: string
    oldContent?: string | null
    file?: FileInfo | null
  }
}

export const eventBus = mitt<AppEvents>()
