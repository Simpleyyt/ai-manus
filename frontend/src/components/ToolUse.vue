<template>
  <p v-if="tool.name === 'message' && tool.args?.text" class="text-[var(--text-secondary)] text-[14px] overflow-hidden text-ellipsis whitespace-pre-line">
    {{ tool.args.text }}
  </p>
  <!-- Official StandardToolUsed: flat icon+label row (not gray pill) -->
  <div
    v-else-if="toolInfo"
    class="flex w-full items-center gap-2 group"
    :class="isCalling ? '' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'">
    <div
      class="flex min-w-0 flex-1 items-center gap-[4px] overflow-hidden leading-[20px] clickable"
      @click="handleClick">
      <div class="w-[20px] inline-flex items-center flex-shrink-0 text-[var(--text-primary)]">
        <component :is="toolInfo.icon" :size="20" />
      </div>
      <div
        class="min-w-0 flex-1 truncate whitespace-nowrap"
        :class="isCalling ? 'shimmer-text-secondary' : ''"
        :title="`${toolInfo.function}${toolInfo.functionArg}`">
        <span class="text-sm">{{ toolInfo.function }}</span>
        <span
          v-if="toolInfo.functionArg"
          class="ms-[6px] font-mono text-[12px]"
          :class="isCalling ? '' : 'text-[var(--text-tertiary)]'">{{ toolInfo.functionArg }}</span>
      </div>
    </div>
    <div class="float-right transition text-[12px] text-[var(--text-tertiary)] invisible group-hover:visible">
      {{ relativeTime(tool.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ToolContent } from "../types/message";
import { useToolInfo } from "../composables/useTool";
import { useRelativeTime } from "../composables/useTime";

const props = defineProps<{
  tool: ToolContent;
}>();

const emit = defineEmits<{
  (e: "click"): void;
}>();

const { relativeTime } = useRelativeTime();
const { toolInfo } = useToolInfo(ref(props.tool));

const isCalling = computed(() => props.tool.status === "calling");

const handleClick = () => {
  emit("click");
};
</script>
