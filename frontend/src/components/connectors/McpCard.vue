<template>
  <div
    class="flex items-center gap-3 p-3 h-[76px] rounded-[12px] border border-[var(--border-main)] clickable hover:bg-[var(--fill-tsp-white-light)]"
    data-testid="mcp-card"
    @click="onCardClick"
  >
    <div
      class="flex items-center justify-center size-10 bg-[var(--background-menu-white)] rounded-lg border border-[var(--border-main)] shrink-0"
    >
      <Cable :size="24" color="var(--icon-primary)" />
    </div>
    <div class="flex flex-col items-start justify-center min-w-0 flex-1">
      <div class="w-full flex gap-1 items-center">
        <p class="truncate min-w-0 text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
          {{ connector.name }}
        </p>
      </div>
    </div>

    <div v-if="canManage" @click.stop>
      <Popover v-model:open="menuOpen">
        <PopoverTrigger as-child>
          <button
            type="button"
            data-testid="mcp-card-actions"
            class="flex items-center justify-center size-7 shrink-0 rounded-[8px] border border-[var(--border-main)] hover:bg-[var(--fill-tsp-white-light)] clickable"
            :title="t('Actions')"
            @click="menuOpen = true"
          >
            <Ellipsis :size="14" color="var(--icon-primary)" />
          </button>
        </PopoverTrigger>
        <PopoverContent
          align="end"
          side="bottom"
          :side-offset="4"
          class="z-[1100] text-[var(--text-primary)] text-sm w-max min-w-[180px] rounded-[12px] border-0 bg-[var(--background-menu-white)] p-1 shadow-menu"
        >
          <button
            type="button"
            data-testid="mcp-card-edit"
            class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
            @click="menuOpen = false; emit('edit', connector)"
          >
            <Pencil :size="16" color="var(--icon-primary)" />
            <span>{{ t('Edit configuration') }}</span>
          </button>
          <button
            type="button"
            data-testid="mcp-card-delete"
            class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--function-error)] hover:bg-[var(--fill-tsp-white-main)]"
            @click="menuOpen = false; emit('delete', connector)"
          >
            <Trash2 :size="16" color="var(--function-error)" />
            <span>{{ t('Delete') }}</span>
          </button>
        </PopoverContent>
      </Popover>
    </div>
    <div
      v-else
      class="flex items-center justify-center size-8 shrink-0"
    >
      <Check :size="16" color="var(--icon-tertiary)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Cable, Check, Ellipsis, Pencil, Trash2 } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import type { Connector } from '@/types/connector'

const props = defineProps<{
  connector: Connector
}>()

const emit = defineEmits<{
  edit: [connector: Connector]
  delete: [connector: Connector]
}>()

const { t } = useI18n()
const menuOpen = ref(false)

const canManage = computed(() => !props.connector.readonly && props.connector.source !== 'file')

const onCardClick = () => {
  if (canManage.value) {
    emit('edit', props.connector)
  }
}
</script>
