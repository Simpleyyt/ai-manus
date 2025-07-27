import { Ref } from 'vue'

export interface LeftPanelState {
  isLeftPanelShow: Ref<boolean>
  toggleLeftPanel: () => void
  setLeftPanel: (visible: boolean) => void
  showLeftPanel: () => void
  hideLeftPanel: () => void
} 