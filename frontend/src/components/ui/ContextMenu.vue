<template>
  <!-- Official DropdownMenu portal chrome (session header … / sidebar row menu) -->
  <div id="context-menu-portal" data-floating-ui-portal="">
    <div
      v-if="contextMenuVisible"
      ref="menuRef"
      data-bottom=""
      class="min-w-max inline-block transition-[transform,opacity,scale] duration-150 data-[starting-style]:opacity-0 data-[ending-style]:opacity-0 data-[starting-style]:-translate-y-2 data-[ending-style]:-translate-y-2"
      tabindex="-1"
      data-floating-ui-focusable=""
      role="dialog"
      :style="{
        position: 'absolute',
        left: calculatedPosition.x + 'px',
        top: calculatedPosition.y + 'px',
        '--available-width': '554px',
        '--available-height': '649px',
        '--anchor-width': '22px',
        '--anchor-height': '22px',
      }">
      <div class="bg-[var(--background-menu-white)] shadow-menu rounded-[12px] p-1 min-w-[172px]">
        <template v-for="item in menuItems" :key="item.key">
          <!-- Official divider: h-[1px] bg-[var(--border-main)] my-[2px] mx-[8px] -->
          <div
            v-if="item.key.startsWith('separator')"
            class="h-[1px] bg-[var(--border-main)] my-[2px] mx-[8px]" />
          <div
            v-else
            class="flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-sm"
            :class="[
              item.variant === 'danger' ? 'text-[var(--function-error)]' : 'text-[var(--text-primary)]',
              item.disabled ? 'opacity-50 cursor-not-allowed hover:bg-transparent' : '',
            ]"
            @click="handleMenuItemClick(item)">
            <div class="size-5 flex items-center justify-center">
              <component
                v-if="item.icon"
                :is="item.icon"
                :size="16"
                :stroke="item.variant === 'danger' ? 'var(--function-error)' : 'var(--icon-primary)'"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round" />
            </div>
            <div class="flex-1 flex items-center gap-2 min-w-0">
              {{ item.label }}
            </div>
            <svg
              v-if="item.checked"
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--icon-primary)"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="lucide lucide-check ms-auto">
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </div>
        </template>
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
  handleMenuItemClick,
} = useContextMenu();

const menuRef = ref<HTMLElement>();

const calculatedPosition = computed(() => {
  if (!targetElement.value) {
    return menuPosition.value;
  }

  const rect = targetElement.value.getBoundingClientRect();
  const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
  const scrollTop = window.scrollY || document.documentElement.scrollTop;

  const centerX = rect.left + scrollLeft + rect.width / 2;
  const menuWidth = menuRef.value?.offsetWidth || 172;

  return {
    x: centerX - menuWidth / 2,
    y: rect.bottom + scrollTop + 4,
  };
});

watch(targetElement, () => {
  if (targetElement.value) {
    menuPosition.value = calculatedPosition.value;
  }
}, { immediate: true });

const handleClickOutside = (event: MouseEvent) => {
  if (!contextMenuVisible.value || !menuRef.value) return;
  const target = event.target as Node;
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
