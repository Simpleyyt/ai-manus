import { ref, watch } from 'vue'
import type { SessionSidebarState } from '../types/panel'

const SESSION_SIDEBAR_STATE_KEY = 'manus-session-sidebar-state'
const LEGACY_LEFT_PANEL_STATE_KEY = 'manus-left-panel-state'

const getInitialSessionSidebarState = (): boolean => {
  try {
    const saved = localStorage.getItem(SESSION_SIDEBAR_STATE_KEY)
    if (saved !== null) {
      return JSON.parse(saved)
    }
    // Migrate from previous LeftPanel key
    const legacy = localStorage.getItem(LEGACY_LEFT_PANEL_STATE_KEY)
    if (legacy !== null) {
      const value = JSON.parse(legacy) as boolean
      localStorage.setItem(SESSION_SIDEBAR_STATE_KEY, JSON.stringify(value))
      localStorage.removeItem(LEGACY_LEFT_PANEL_STATE_KEY)
      return value
    }
    return false
  } catch (error) {
    console.error('Failed to read session sidebar state from localStorage:', error)
    return false
  }
}

const isSessionSidebarShow = ref(getInitialSessionSidebarState())

const saveSessionSidebarState = (state: boolean) => {
  try {
    localStorage.setItem(SESSION_SIDEBAR_STATE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('Failed to save session sidebar state to localStorage:', error)
  }
}

watch(isSessionSidebarShow, (newValue) => {
  saveSessionSidebarState(newValue)
}, { immediate: false })

export function useSessionSidebar(): SessionSidebarState {
  const toggleSessionSidebar = () => {
    isSessionSidebarShow.value = !isSessionSidebarShow.value
  }

  const setSessionSidebar = (visible: boolean) => {
    isSessionSidebarShow.value = visible
  }

  const showSessionSidebar = () => {
    isSessionSidebarShow.value = true
  }

  const hideSessionSidebar = () => {
    isSessionSidebarShow.value = false
  }

  return {
    isSessionSidebarShow,
    toggleSessionSidebar,
    setSessionSidebar,
    showSessionSidebar,
    hideSessionSidebar,
  }
}
