<template>
  <!-- Official nested step chat / notify under StepGroup timeline -->
  <div
    v-if="tool.name === 'message' && tool.args?.text"
    class="flex flex-col gap-2 w-full">
    <p class="text-[var(--text-secondary)] text-[14px] m-0 u-break-words whitespace-pre-wrap">
      {{ tool.args.text }}
    </p>
  </div>
  <!--
    Official StandardToolUsed (mined tN):
    brief ? MiddleTruncate(brief)
         : message ? action + optional mono param
    Streaming / active → shimmer-text-secondary (continuous, Thinking cadence).
  -->
  <div
    v-else-if="toolInfo"
    class="flex w-full items-center gap-2 group"
    :class="showShimmer ? '' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'">
    <div
      class="flex min-w-0 flex-1 items-center overflow-hidden leading-[20px] gap-[4px] clickable"
      @click="handleClick">
      <div class="w-[20px] inline-flex items-center flex-shrink-0 text-[var(--text-primary)]">
        <component :is="toolInfo.icon" :size="20" />
      </div>
      <!-- Keep one text node while shimmering so the CSS animation is not remounted. -->
      <div
        v-if="briefText"
        class="min-w-0 flex-1 truncate text-sm"
        :class="showShimmer ? 'shimmer-text-secondary' : ''"
        :title="briefText">
        {{ briefText }}
      </div>
      <div
        v-else
        class="min-w-0 flex-1 truncate whitespace-nowrap"
        :class="showShimmer ? 'shimmer-text-secondary' : ''"
        :title="timelineLabel">
        <span class="text-sm">{{ toolInfo.function }}</span>
        <span
          v-if="toolInfo.functionArg"
          class="ms-[6px] font-mono text-[12px]"
          :class="showShimmer ? '' : 'text-[var(--text-tertiary)]'">{{ toolInfo.functionArg }}</span>
      </div>
    </div>
    <div class="float-right transition text-[12px] leading-[16px] text-[var(--text-tertiary)] invisible group-hover:visible">
      {{ relativeTime(tool.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import { ToolContent } from "../types/message";
import { useToolInfo } from "../composables/useTool";
import { useToolShimmer } from "../composables/useToolShimmer";
import { useRelativeTime } from "../composables/useTime";

const props = defineProps<{
  tool: ToolContent;
  /** Keep shimmering while this row is the live tool of a running step. */
  active?: boolean;
}>();

const emit = defineEmits<{
  (e: "click"): void;
}>();

const { relativeTime } = useRelativeTime();
const toolRef = toRef(props, "tool");
const { toolInfo } = useToolInfo(toolRef);
const statusRef = computed(() => props.tool.status);
const activeRef = computed(() => !!props.active);
const { showShimmer } = useToolShimmer(statusRef, activeRef);

const briefText = computed(() => (props.tool.brief || "").trim());

const timelineLabel = computed(() => {
  if (briefText.value) return briefText.value;
  const action = toolInfo.value?.function || "";
  const param = toolInfo.value?.functionArg || "";
  return param ? `${action} ${param}` : action;
});

const handleClick = () => {
  emit("click");
};
</script>
