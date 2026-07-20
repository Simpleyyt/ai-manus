import { Ref } from 'vue'

export interface SessionSidebarState {
  isSessionSidebarShow: Ref<boolean>
  toggleSessionSidebar: () => void
  setSessionSidebar: (visible: boolean) => void
  showSessionSidebar: () => void
  hideSessionSidebar: () => void
}
