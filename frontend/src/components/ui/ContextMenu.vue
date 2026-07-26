<template>
  <!-- Official DropdownMenu portal chrome (session header … / sidebar row menu) -->
  <Teleport to="body">
    <div id="context-menu-portal" data-floating-ui-portal="" class="relative z-[1100]">
      <div
        v-if="contextMenuVisible"
        ref="menuRef"
        class="z-[1100] min-w-max inline-block transition-[transform,opacity,scale] duration-150 data-[starting-style]:opacity-0 data-[ending-style]:opacity-0 data-[starting-style]:-translate-y-2 data-[ending-style]:-translate-y-2"
        tabindex="-1"
        data-floating-ui-focusable=""
        role="dialog"
        :style="menuStyle">
        <div class="bg-[var(--background-menu-white)] shadow-menu rounded-[12px] p-1 min-w-[172px]">
          <template v-for="item in menuItems" :key="item.key">
            <!-- Official divider: h-[1px] bg-[var(--border-main)] my-[2px] mx-[8px] -->
            <div
              v-if="item.key.startsWith('separator')"
              class="h-[1px] bg-[var(--border-main)] my-[2px] mx-[8px]" />

            <!-- Official Move-to-project style submenu (Popover + chevron) -->
            <Popover
              v-else-if="item.children"
              :open="openSubmenuKey === item.key"
              @update:open="(v: boolean) => { openSubmenuKey = v ? item.key : null }">
              <PopoverTrigger as-child>
                <div
                  class="group"
                  aria-haspopup="dialog"
                  :aria-expanded="openSubmenuKey === item.key"
                  :data-popover-trigger="openSubmenuKey === item.key ? 'true' : undefined"
                  @mouseenter="openSubmenuKey = item.key"
                  @click.prevent.stop="openSubmenuKey = item.key">
                  <div
                    class="flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm group-data-[popover-trigger]:bg-[var(--fill-tsp-white-main)]">
                    <div class="size-5 flex items-center justify-center">
                      <component
                        v-if="item.icon"
                        :is="item.icon"
                        :size="16"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round" />
                    </div>
                    <div class="flex-1 flex items-center gap-2 min-w-0">
                      <div class="flex items-center justify-between flex-1 gap-[8px]">
                        <span>{{ item.label }}</span>
                        <ChevronRight :size="16" color="var(--icon-secondary)" />
                      </div>
                    </div>
                  </div>
                </div>
              </PopoverTrigger>
              <!-- Official: shadow-menu rounded-[12px] min-w-[110px] p-1 max-h-[400px] overflow-y-auto w-[225px] -->
              <PopoverContent
                side="right"
                align="start"
                :side-offset="4"
                class="z-[1100] w-[225px] min-w-[110px] max-h-[400px] overflow-y-auto rounded-[12px] border-0 bg-[var(--background-menu-white)] p-1 shadow-menu"
                @mouseenter="openSubmenuKey = item.key">
                <template v-for="child in item.children" :key="child.key">
                  <div
                    v-if="child.key.startsWith('separator')"
                    class="h-[1px] bg-[var(--border-main)] my-[2px] mx-[8px]" />
                  <div
                    v-else
                    class="flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm"
                    @click="handleMenuItemClick(child)">
                    <div class="flex-1 flex items-center gap-2 min-w-0">
                      <component
                        v-if="child.icon"
                        :is="child.icon"
                        :size="16"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="flex-shrink-0" />
                      <span class="truncate" :title="child.label">{{ child.label }}</span>
                    </div>
                    <svg
                      v-if="child.checked"
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="var(--icon-primary)"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      class="lucide lucide-check ms-auto flex-shrink-0">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  </div>
                </template>
              </PopoverContent>
            </Popover>

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
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { ChevronRight } from 'lucide-vue-next';
import { useContextMenu } from '@/composables/useContextMenu';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

const {
  contextMenuVisible,
  menuItems,
  targetElement,
  hideContextMenu,
  handleMenuItemClick,
} = useContextMenu();

const menuRef = ref<HTMLElement>();
const openSubmenuKey = ref<string | null>(null);

/**
 * Official floating UI for session-header … menu (CDP dump):
 *   position: fixed
 *   left = trigger.right - menuWidth   // end / right-edge align
 *   top  = trigger.bottom + 4
 *   --available-width / --available-height / --anchor-width / --anchor-height
 * Local used to center under the trigger → overflow past the right edge of the viewport.
 */
const floating = ref({
  x: 0,
  y: 0,
  availableWidth: 0,
  availableHeight: 0,
  anchorWidth: 22,
  anchorHeight: 22,
});

const menuStyle = computed(() => ({
  position: 'fixed' as const,
  left: `${floating.value.x}px`,
  top: `${floating.value.y}px`,
  '--available-width': `${floating.value.availableWidth}px`,
  '--available-height': `${floating.value.availableHeight}px`,
  '--anchor-width': `${floating.value.anchorWidth}px`,
  '--anchor-height': `${floating.value.anchorHeight}px`,
}));

const updateFloatingPosition = () => {
  if (!targetElement.value) return;
  const rect = targetElement.value.getBoundingClientRect();
  const menuWidth = menuRef.value?.offsetWidth || 172;
  const menuHeight = menuRef.value?.offsetHeight || 0;
  const gap = 4;
  const pad = 8;

  // Official: align end (menu.right === trigger.right)
  let x = rect.right - menuWidth;
  let y = rect.bottom + gap;

  // Keep inside viewport (floating-ui shift)
  x = Math.min(Math.max(pad, x), window.innerWidth - menuWidth - pad);
  if (menuHeight > 0) {
    y = Math.min(Math.max(pad, y), window.innerHeight - menuHeight - pad);
  }

  floating.value = {
    x,
    y,
    availableWidth: Math.max(0, window.innerWidth - x),
    availableHeight: Math.max(0, window.innerHeight - y),
    anchorWidth: rect.width,
    anchorHeight: rect.height,
  };
};

watch(contextMenuVisible, async (v) => {
  if (!v) {
    openSubmenuKey.value = null;
    return;
  }
  await nextTick();
  updateFloatingPosition();
  // Re-measure after paint once real menu width is known
  requestAnimationFrame(() => updateFloatingPosition());
});

watch(targetElement, async () => {
  if (contextMenuVisible.value && targetElement.value) {
    await nextTick();
    updateFloatingPosition();
  }
});

const handleClickOutside = (event: MouseEvent) => {
  if (!contextMenuVisible.value || !menuRef.value) return;
  const target = event.target as Node;
  if (targetElement.value?.contains(target)) return;
  if (menuRef.value.contains(target)) return;
  // Nested PopoverContent is portaled — keep menu open while interacting with it
  const el = target as HTMLElement;
  if (el.closest?.('[data-slot="popover-content"]')) return;
  hideContextMenu();
};

const handleViewportChange = () => {
  if (contextMenuVisible.value) updateFloatingPosition();
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  window.addEventListener('resize', handleViewportChange);
  window.addEventListener('scroll', handleViewportChange, true);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', handleViewportChange);
  window.removeEventListener('scroll', handleViewportChange, true);
});
</script>
