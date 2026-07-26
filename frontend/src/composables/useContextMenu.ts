import { ref, markRaw } from 'vue'

export interface MenuItem {
    key: string;
    label: string;
    icon?: any; // Vue component or SVG
    variant?: 'default' | 'danger';
    checked?: boolean;
    disabled?: boolean;
    action?: (itemId: string) => void;
}

// Global state for context menu
const contextMenuVisible = ref(false)
const selectedItemId = ref<string>()
const menuPosition = ref({ x: 0, y: 0 })
const menuItems = ref<MenuItem[]>([])
const menuItemClickHandler = ref<((itemKey: string, itemId: string) => void) | null>(null)
const onCloseHandler = ref<((itemId: string) => void) | null>(null)
const targetElement = ref<HTMLElement | null>(null)

export function useContextMenu() {
  // Show context menu with specific menu items
  const showContextMenu = (
    itemId: string, 
    element: HTMLElement,
    items: MenuItem[],
    onMenuItemClick?: (itemKey: string, itemId: string) => void,
    onClose?: (itemId: string) => void
  ) => {
    hideContextMenu()
    selectedItemId.value = itemId
    targetElement.value = element
    menuItems.value = items
    menuItemClickHandler.value = onMenuItemClick || null
    onCloseHandler.value = onClose || null
    contextMenuVisible.value = true
  }

  // Hide context menu
  const hideContextMenu = () => {
    const currentItemId = selectedItemId.value
    const currentOnCloseHandler = onCloseHandler.value
    
    contextMenuVisible.value = false
    selectedItemId.value = undefined
    menuItems.value = []
    menuItemClickHandler.value = null
    onCloseHandler.value = null
    targetElement.value = null
    
    // Call onClose callback if provided
    if (currentOnCloseHandler && currentItemId) {
      currentOnCloseHandler(currentItemId)
    }
  }

  // Handle menu item click (called from ContextMenu component)
  const handleMenuItemClick = (item: MenuItem) => {
    if (item.disabled) return;
    
    if (selectedItemId.value) {
      // Call the provided handler
      if (menuItemClickHandler.value) {
        menuItemClickHandler.value(item.key, selectedItemId.value);
      }
      
      // Execute action if provided
      if (item.action) {
        item.action(selectedItemId.value);
      }
    }
    
    hideContextMenu();
  }

  return {
    // Reactive state
    contextMenuVisible,
    selectedItemId,
    menuPosition,
    menuItems,
    targetElement,
    
    // Actions
    showContextMenu,
    hideContextMenu,
    handleMenuItemClick
  }
}

// Utility functions for creating common menu items
export const createMenuItem = (
  key: string,
  label: string,
  options: Partial<Omit<MenuItem, 'key' | 'label'>> = {}
): MenuItem => ({
  key,
  label,
  variant: 'default',
  ...options,
  icon: options.icon ? markRaw(options.icon) : options.icon
})

export const createDangerMenuItem = (
  key: string,
  label: string,
  options: Partial<Omit<MenuItem, 'key' | 'label' | 'variant'>> = {}
): MenuItem => ({
  key,
  label,
  variant: 'danger',
  ...options,
  icon: options.icon ? markRaw(options.icon) : options.icon
})

export const createSeparator = (): MenuItem => ({
  key: `separator-${Math.random().toString(36).slice(2)}`,
  label: '',
  disabled: true,
}) 