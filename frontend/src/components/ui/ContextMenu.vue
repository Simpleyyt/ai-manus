<template>
    <div id="context-menu-portal" data-floating-ui-portal="">
        <div v-if="contextMenuVisible" ref="menuRef" data-bottom=""
            class="min-w-max inline-block transition-[transform,opacity,scale] duration-150 data-[starting-style]:opacity-0 data-[ending-style]:opacity-0 data-[starting-style]:-translate-y-2 data-[ending-style]:-translate-y-2"
            tabindex="-1" data-floating-ui-focusable="" role="dialog" :style="{
                position: 'absolute',
                left: calculatedPosition.x + 'px',
                top: calculatedPosition.y + 'px',
                '--available-width': '554px',
                '--available-height': '649px',
                '--anchor-width': '22px',
                '--anchor-height': '22px'
            }">
            <div
                class="bg-[var(--background-menu-white)] shadow-[0_4px_11px_0px_var(--shadow-S)] rounded-xl border border-[var(--border-dark)] dark:border-[var(--border-light)] min-w-[126px]">
                <div class="p-1">
                    <div v-for="item in menuItems" :key="item.key" @click="handleMenuItemClick(item)"
                        class="flex items-center gap-3 w-full px-3 py-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-sm"
                        :class="[
                            item.variant === 'danger' ? 'text-[var(--function-error)]' : 'text-[var(--text-primary)]',
                            item.disabled ? 'opacity-50 cursor-not-allowed' : ''
                        ]">
                        <div class="flex-1 flex items-center gap-3">
                            <component v-if="item.icon" :is="item.icon" 
                                class="w-4 h-4" 
                                :stroke="item.variant === 'danger' ? 'var(--function-error)' : 'var(--icon-primary)'"
                                stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                            {{ item.label }}
                            <svg v-if="item.checked" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                                fill="none" stroke="var(--icon-primary)" stroke-width="2" stroke-linecap="round"
                                stroke-linejoin="round" class="lucide lucide-check ml-auto">
                                <path d="M20 6 9 17l-5-5"></path>
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useContextMenu } from '@/composables/useContextMenu';

const { 
    contextMenuVisible, 
    menuPosition, 
    menuItems, 
    targetElement,
    hideContextMenu, 
    handleMenuItemClick 
} = useContextMenu();

const menuRef = ref<HTMLElement>();

// Calculate menu position based on target element
const calculatedPosition = computed(() => {
    if (!targetElement.value) {
        return menuPosition.value;
    }
    
    const rect = targetElement.value.getBoundingClientRect();
    const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    
    // Calculate center position and adjust for menu width
    const centerX = rect.left + scrollLeft + rect.width / 2;
    const menuWidth = menuRef.value?.offsetWidth || 126; // fallback to min-width
    
    return {
        x: centerX - menuWidth / 2,
        y: rect.bottom + scrollTop + 4 // 4px offset below the element
    };
});

// Update menuPosition when target element changes
watch(targetElement, () => {
    if (targetElement.value) {
        menuPosition.value = calculatedPosition.value;
    }
}, { immediate: true });

// Handle click outside to close menu
const handleClickOutside = (event: MouseEvent) => {
    if (!contextMenuVisible.value || !menuRef.value) return;
    const target = event.target as Node;
    // Ignore the anchor that opened the menu (same click that opens it).
    if (targetElement.value?.contains(target)) return;
    if (!menuRef.value.contains(target)) {
        hideContextMenu();
    }
};

onMounted(() => {
    document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside);
});
</script> 