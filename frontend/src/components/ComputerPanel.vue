<template>
  <div
    ref="computerPanelRef"
    v-if="visible"
    :class="{
      'h-full w-full top-0 ltr:right-0 rtl:left-0 z-50 fixed sm:sticky sm:top-0 sm:right-0 sm:h-[100vh] sm:min-w-[520px]': isShow,
      'h-full overflow-hidden': !isShow
    }"
    :style="{ 'width': isShow ? `${Math.min(Math.max(parentSize / 2, Math.min(520, parentSize || 520)), parentSize || 520)}px` : '0px', 'opacity': isShow ? '1' : '0', 'transition': '0.2s ease-in-out' }">
    <div class="h-full" :style="{ 'width': isShow ? '100%' : '0px' }">
      <ComputerPanelContent
        v-if="isShow && toolContent"
        :sessionId="sessionId"
        :realTime="realTime"
        :toolContent="toolContent"
        :live="live"
        :isShare="isShare"
        :toolHistory="toolHistory"
        :plan="plan"
        @hide="hideComputerPanel"
        @jumpToRealTime="jumpToRealTime"
        @selectTool="onSelectTool"
        @useComputer="onUseComputer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { ToolContent } from '../types/message'
import type { PlanEventData } from '../types/event'
import ComputerPanelContent from './ComputerPanelContent.vue'
import { useResizeObserver } from '../composables/useResizeObserver'
import { eventBus } from '../utils/eventBus'
import { EVENT_SHOW_FILE_PANEL, EVENT_SHOW_COMPUTER_PANEL } from '../constants/event'

const computerPanelRef = ref<HTMLElement>()
const { size: parentSize } = useResizeObserver(computerPanelRef, {
  target: 'parent',
  property: 'width'
})

const isShow = ref(false)
const live = ref(false)
const toolContent = ref<ToolContent>()
const visible = ref(true)

const emit = defineEmits<{
  (e: 'jumpToRealTime'): void
  (e: 'selectTool', tool: ToolContent): void
  (e: 'useComputer'): void
}>()

defineProps<{
  sessionId?: string
  realTime: boolean
  isShare: boolean
  toolHistory?: ToolContent[]
  plan?: PlanEventData | null
}>()

const showComputerPanel = (content: ToolContent, isLive: boolean = false) => {
  eventBus.emit(EVENT_SHOW_COMPUTER_PANEL)
  visible.value = true
  toolContent.value = content
  isShow.value = true
  live.value = isLive
}

const hideComputerPanel = () => {
  isShow.value = false
}

const jumpToRealTime = () => {
  emit('jumpToRealTime')
}

const onSelectTool = (tool: ToolContent) => {
  toolContent.value = tool
  live.value = false
  emit('selectTool', tool)
}

const onUseComputer = () => {
  emit('useComputer')
}

onMounted(() => {
  eventBus.on(EVENT_SHOW_FILE_PANEL, () => {
    visible.value = false
  })
})

onUnmounted(() => {
  eventBus.off(EVENT_SHOW_FILE_PANEL)
})

defineExpose({
  showComputerPanel,
  hideComputerPanel,
  isShow
})
</script>
