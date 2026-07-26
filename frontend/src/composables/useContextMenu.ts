import { ref, markRaw } from 'vue'

export interface MenuItem {
    key: string;
    label: string;
    icon?: any; // Vue component or SVG
    variant?: 'default' | 'danger';
    checked?: boolean;
    disabled?: boolean;
    /** Official nested popover submenu (e.g. Move to project) */
    children?: MenuItem[];
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
    // Parent rows with children open a submenu — do not dismiss
    if (item.children?.length) return;
    
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

function markIcons(item: MenuItem): MenuItem {
  return {
    ...item,
    icon: item.icon ? markRaw(item.icon) : item.icon,
    children: item.children?.map(markIcons),
  }
}

// Utility functions for creating common menu items
export const createMenuItem = (
  key: string,
  label: string,
  options: Partial<Omit<MenuItem, 'key' | 'label'>> = {}
): MenuItem => markIcons({
  key,
  label,
  variant: 'default',
  ...options,
})

export const createDangerMenuItem = (
  key: string,
  label: string,
  options: Partial<Omit<MenuItem, 'key' | 'label' | 'variant'>> = {}
): MenuItem => markIcons({
  key,
  label,
  variant: 'danger',
  ...options,
})

export const createSubmenuItem = (
  key: string,
  label: string,
  children: MenuItem[],
  options: Partial<Omit<MenuItem, 'key' | 'label' | 'children'>> = {}
): MenuItem => markIcons({
  key,
  label,
  variant: 'default',
  children,
  ...options,
})

export const createSeparator = (): MenuItem => ({
  key: `separator-${Math.random().toString(36).slice(2)}`,
  label: '',
  disabled: true,
})
