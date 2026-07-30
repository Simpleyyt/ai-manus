import { ref } from 'vue'

export type SettingsTabId =
  | 'general'
  | 'account'
  | 'shortcuts'
  | 'personalization'
  | 'help'

const isSettingsDialogOpen = ref(false)
const defaultTab = ref<SettingsTabId>('general')

export function useSettingsDialog() {
  const openSettingsDialog = (tabId?: SettingsTabId | string) => {
    if (tabId === 'settings') {
      defaultTab.value = 'general'
    } else if (
      tabId === 'general'
      || tabId === 'account'
      || tabId === 'shortcuts'
      || tabId === 'personalization'
      || tabId === 'help'
    ) {
      defaultTab.value = tabId
    }
    isSettingsDialogOpen.value = true
  }

  const closeSettingsDialog = () => {
    isSettingsDialogOpen.value = false
  }

  const toggleSettingsDialog = () => {
    isSettingsDialogOpen.value = !isSettingsDialogOpen.value
  }

  const setDefaultTab = (tabId: SettingsTabId) => {
    defaultTab.value = tabId
  }

  return {
    isSettingsDialogOpen,
    defaultTab,
    openSettingsDialog,
    closeSettingsDialog,
    toggleSettingsDialog,
    setDefaultTab,
  }
}
