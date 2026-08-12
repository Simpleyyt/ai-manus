<template>
  <!--
    Official e9 (ChatQuestion shell, non-agent): flex flex-col group mt-6 w-full items-end
    → max-w-[90%] → bubble (t2) → e4 toolbar below
    e4: flex items-center justify-end gap-[2px] overflow-hidden invisible group-hover:visible py-[2px]
         CopyChatEvent (default size-7) + EventTimestamp
  -->
  <div v-if="message.type === 'user'" class="flex flex-col group mt-6 w-full items-end">
    <div class="max-w-[90%]">
      <div class="flex relative flex-col gap-2 max-w-full items-end">
        <ChatAttachmentList
          v-if="userAttachments.length"
          :attachments="userAttachments"
          align-end
        />
        <div v-if="hasUserText" class="relative max-w-full w-fit">
          <div
            data-chat-question-bubble
            class="relative overflow-hidden rounded-[12px] p-3 bg-[var(--fill-white)] dark:bg-[var(--fill-tsp-white-main)] ltr:rounded-br-none rtl:rounded-bl-none border border-[var(--border-main)] dark:border-0 limited-markdown-content text-[var(--text-primary)] u-break-words [&_p]:m-0 [&_p]:leading-[22px] [&>*:first-child]:mt-0 [&>*:last-child]:mb-0"
            v-html="renderMarkdown(messageContent.content)">
          </div>
        </div>
      </div>
      <div class="flex items-center justify-end gap-[2px] overflow-hidden invisible group-hover:visible py-[2px]">
        <ChatMessageCopyButton v-if="hasUserText" :text="plainText" />
        <div class="float-right transition text-[12px] leading-[16px] text-[var(--text-tertiary)] whitespace-nowrap">
          {{ relativeTime(messageContent.timestamp) }}
        </div>
      </div>
    </div>
  </div>
  <!-- Official ChatReplyLayout: gap-2 w-full group mt-3 + header h-[26px] + Logo/ProductName/Lite -->
  <div v-else-if="message.type === 'assistant'" class="flex flex-col gap-2 w-full group" :class="hideAssistantHeader ? 'mt-0' : 'mt-3'">
    <div v-if="!hideAssistantHeader" class="flex items-center justify-between h-[26px] group">
      <div class="flex items-center gap-[8px] -ms-[2px] max-w-full">
        <component v-if="assistantIcon" :is="assistantIcon" :size="24" class="w-6 h-6" />
        <Bot v-else :size="24" class="w-6 h-6" />
        <span v-if="assistantName" class="text-base text-[var(--text-primary)] tracking-tight leading-none">{{ assistantName }}</span>
        <template v-else-if="!assistantIcon">
          <ManusTextIcon />
        </template>
        <span
          v-if="showLiteBadge"
          class="text-[var(--text-tertiary)] text-xs flex h-5 py-0.5 px-1.5 items-center gap-1 rounded-[6px] border border-[var(--border-dark)] flex-shrink-0 ml-[3px]">
          Lite
        </span>
      </div>
      <div class="flex items-center gap-[2px] invisible group-hover:visible">
        <div class="float-right transition text-[12px] text-[var(--text-tertiary)]">
          {{ relativeTime(message.content.timestamp) }}
        </div>
      </div>
    </div>
    <div
      class="limited-markdown-content w-full text-[var(--text-primary)] u-break-words [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 prose prose-sm sm:prose-base dark:prose-invert max-w-none p-0 m-0 [&_pre:not(.shiki)]:!bg-[var(--fill-tsp-white-light)] [&_pre:not(.shiki)]:text-[var(--text-primary)]"
      v-html="renderMarkdown(messageContent.content)"></div>
    <!-- Official ChatReplyActions: Copy (Fork skipped). Hide on last live reply when TaskCompleted footer shows. -->
    <div
      v-if="showCopyActions"
      class="flex items-center flex-wrap gap-[12px]"
      :class="isLastBeforeUser ? 'pb-2' : 'pb-5'">
      <div class="flex items-center gap-[2px]">
        <ChatMessageCopyButton :text="plainText" button-class="size-[28px]" />
      </div>
    </div>
  </div>
  <ToolUse
    v-else-if="message.type === 'tool'"
    :tool="toolContent"
    :active="toolContent.status === 'calling'"
    @click="handleToolClick(toolContent)"
  />
  <!-- Official StepGroup: empty:pb-0 + pb-0 when next list item is also stepGroup -->
  <div
    v-else-if="message.type === 'step'"
    class="flex flex-col empty:pb-0"
    :class="stepConnectsToNext ? 'pb-0' : 'pb-2'">
    <div class="flex flex-col">
      <component
        :is="stepCanToggle ? 'button' : 'div'"
        :type="stepCanToggle ? 'button' : undefined"
        class="relative flex h-[28px] w-full min-w-0 items-center overflow-hidden whitespace-nowrap text-[14px] font-normal text-[var(--text-secondary)]"
        :class="stepCanToggle
          ? 'group/header clickable hover:text-[var(--text-primary)] border-0 bg-transparent p-0 text-start'
          : undefined"
        @click="stepCanToggle ? (stepExpanded = !stepExpanded) : undefined"
      >
        <div class="flex min-w-0 flex-1 flex-nowrap items-center gap-[4px] overflow-hidden">
          <div class="flex size-[20px] flex-shrink-0 items-center justify-center rounded-[100px]">
            <div
              v-if="stepCompleted"
              class="bg-[var(--fill-tsp-white-dark)] rounded-full size-[17px] flex items-center justify-center"
            >
              <StepCheckIcon :size="9" class="text-[var(--icon-tertiary)]" />
            </div>
            <LiveStatusCanvas v-else :size="16" :active="stepContent.status === 'running'" />
          </div>
          <div class="flex min-w-0 flex-1 items-center justify-start gap-[4px] overflow-hidden py-[4px]">
            <span class="min-w-0 max-w-full overflow-hidden text-ellipsis whitespace-nowrap leading-[20px]">
              {{ stepContent.description }}
            </span>
            <span
              v-if="stepCanToggle"
              class="hidden size-[16px] flex-shrink-0 items-center justify-center group-hover/header:flex"
              :class="(!stepCompleted || stepExpanded) ? 'flex' : undefined"
            >
              <ChevronDown v-if="stepExpanded" :size="16" color="currentColor" />
              <ChevronRight v-else :size="16" color="currentColor" />
            </span>
          </div>
        </div>
        <div
          class="float-right transition text-[12px] leading-[16px] text-[var(--text-tertiary)] ms-auto flex-shrink-0"
          :class="stepCanToggle ? 'invisible group-hover/header:visible' : undefined"
        >
          {{ relativeTime(message.content.timestamp) }}
        </div>
      </component>
      <!-- Official: collapsed → lastToolItems only (while live); expanded → preceding + last -->
      <div v-if="stepHasTimelineBody" class="flex min-w-0 flex-col">
        <div class="relative min-w-0">
          <div class="pointer-events-none absolute inset-y-0 start-0 flex w-[20px] justify-center py-2">
            <div class="h-full w-px flex-none bg-[var(--border-main)]"></div>
          </div>
          <div class="flex min-w-0 flex-col ps-[20px]">
            <div class="min-w-0 overflow-hidden" style="height: auto; opacity: 1">
              <div class="min-w-0">
                <div class="flex min-w-0 flex-col">
                  <div
                    v-for="item in stepVisiblePreceding"
                    :key="item.id"
                    class="min-w-0 [&:has(>[data-timeline-content]:empty)]:hidden"
                    style="opacity: 1; transform: none"
                  >
                    <div data-timeline-content="true" class="min-w-0 flex-1 py-1 ps-[4px]">
                      <ToolUse
                        v-if="item.kind === 'tool'"
                        :tool="item.tool"
                        :active="isLiveStepTool(item.id)"
                        @click="handleToolClick(item.tool)"
                      />
                    </div>
                  </div>
                  <div
                    v-for="item in stepVisibleLast"
                    :key="item.id"
                    class="min-w-0 [&:has(>[data-timeline-content]:empty)]:hidden"
                    style="opacity: 1; transform: none"
                  >
                    <div data-timeline-content="true" class="min-w-0 flex-1 py-1 ps-[4px]">
                      <ToolUse
                        v-if="item.kind === 'tool'"
                        :tool="item.tool"
                        :active="isLiveStepTool(item.id)"
                        @click="handleToolClick(item.tool)"
                      />
                      <div v-else class="flex flex-col gap-2 w-full">
                        <p class="text-[var(--text-secondary)] text-[14px] u-break-words whitespace-pre-wrap m-0">
                          {{ item.text }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="message.type === 'attachments' && attachmentsContent.role === 'assistant'" class="flex flex-col gap-2 w-full group" :class="hideAssistantHeader ? 'mt-0' : 'mt-3'">
    <div v-if="!hideAssistantHeader" class="flex items-center justify-between h-[26px] group">
      <div class="flex items-center gap-[8px] -ms-[2px] max-w-full">
        <component v-if="assistantIcon" :is="assistantIcon" :size="24" class="w-6 h-6" />
        <Bot v-else :size="24" class="w-6 h-6" />
        <span v-if="assistantName" class="text-base text-[var(--text-primary)] tracking-tight leading-none">{{ assistantName }}</span>
        <template v-else-if="!assistantIcon">
          <ManusTextIcon />
        </template>
        <span
          v-if="showLiteBadge"
          class="text-[var(--text-tertiary)] text-xs flex h-5 py-0.5 px-1.5 items-center gap-1 rounded-[6px] border border-[var(--border-dark)] flex-shrink-0 ml-[3px]">
          Lite
        </span>
      </div>
      <div class="flex items-center gap-[2px] invisible group-hover:visible">
        <div class="float-right transition text-[12px] text-[var(--text-tertiary)]">
          {{ relativeTime(attachmentsContent.timestamp) }}
        </div>
      </div>
    </div>
    <AttachmentsMessage :content="attachmentsContent" :hideAllFilesButton="hideAllFilesButton"/>
  </div>
  <AttachmentsMessage v-else-if="message.type === 'attachments'" :content="attachmentsContent" :hideAllFilesButton="hideAllFilesButton"/>
</template>

<script setup lang="ts">
import ManusTextIcon from './icons/ManusTextIcon.vue';
import {
  Message,
  MessageContent,
  AttachmentsContent,
  resolveStepTimelineVisibility,
} from '../types/message';
import ToolUse from './ToolUse.vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { computed, ref, type Component } from 'vue';
import { ToolContent, StepContent } from '../types/message';
import { useRelativeTime } from '../composables/useTime';
import { Bot, ChevronDown, ChevronRight } from 'lucide-vue-next';
import AttachmentsMessage from './AttachmentsMessage.vue';
import ChatMessageCopyButton from './ChatMessageCopyButton.vue';
import ChatAttachmentList from './ChatAttachmentList.vue';
import LiveStatusCanvas from './LiveStatusCanvas.vue';
import StepCheckIcon from './icons/StepCheckIcon.vue';


const props = defineProps<{
  message: Message;
  sessionId?: string;
  assistantIcon?: Component;
  assistantName?: string;
  hideAllFilesButton?: boolean;
  hideHeader?: boolean;
  /** Official ChatReplyLayout Lite badge (qualityMode === lite / chat) */
  showLiteBadge?: boolean;
  /** Official ChatReplyActions: show Copy under this assistant reply */
  showCopyActions?: boolean;
  /** Official: pb-2 when last reply before a user message */
  isLastBeforeUser?: boolean;
  /** Official StepGroup: pb-0 when the next list item is also a step */
  stepConnectsToNext?: boolean;
}>();

const hideAssistantHeader = computed(() => props.hideHeader ?? false);
const showLiteBadge = computed(() => props.showLiteBadge ?? false);
const showCopyActions = computed(() => props.showCopyActions ?? false);
const isLastBeforeUser = computed(() => props.isLastBeforeUser ?? false);
const stepConnectsToNext = computed(() => props.stepConnectsToNext ?? false);

const emit = defineEmits<{
  (e: 'toolClick', tool: ToolContent): void;
}>();

const handleToolClick = (tool: ToolContent) => {
  emit('toolClick', tool);
};

// For backward compatibility, provide the original computed properties
const stepContent = computed(() => props.message.content as StepContent);
const stepCompleted = computed(() =>
  stepContent.value.status === 'completed' || stepContent.value.status === 'failed',
);
const stepVisibility = computed(() => resolveStepTimelineVisibility(stepContent.value));
/** Official: canToggle when some timeline rows stay hidden while collapsed. */
const stepCanToggle = computed(() => stepVisibility.value.canToggle);
/**
 * Official StepGroup: default collapsed (ChevronRight). While live, collapsed
 * still shows lastToolItems; expand reveals precedingItems + last.
 */
const stepExpanded = ref(false);
const stepVisiblePreceding = computed(() =>
  stepExpanded.value ? stepVisibility.value.precedingItems : [],
);
const stepVisibleLast = computed(() => {
  const { lastToolItems, collapsedVisibleItems } = stepVisibility.value;
  if (lastToolItems.length === 0) return [];
  if (stepExpanded.value) return lastToolItems;
  return collapsedVisibleItems;
});
const stepHasTimelineBody = computed(
  () => stepVisiblePreceding.value.length > 0 || stepVisibleLast.value.length > 0,
);

/** Current (last) tool of a running step — keep its label shimmering continuously. */
const liveStepToolId = computed(() => {
  if (stepCompleted.value) return null;
  for (let i = stepVisibility.value.lastToolItems.length - 1; i >= 0; i -= 1) {
    const item = stepVisibility.value.lastToolItems[i];
    if (item.kind === 'tool') return item.id;
  }
  return null;
});

const isLiveStepTool = (id: string) => liveStepToolId.value === id;

const messageContent = computed(() => props.message.content as MessageContent);
const toolContent = computed(() => props.message.content as ToolContent);
const attachmentsContent = computed(() => props.message.content as AttachmentsContent);

const userAttachments = computed(() => messageContent.value.attachments ?? []);
const hasUserText = computed(() => !!(messageContent.value.content || '').trim());

const plainText = computed(() => {
  if (props.message.type === 'user' || props.message.type === 'assistant') {
    return (messageContent.value.content || '').trim();
  }
  return '';
});

const { relativeTime } = useRelativeTime();

const renderer = new marked.Renderer();
renderer.link = ({ href, title, text }: { href: string; title?: string | null; text: string }) => {
  const titleAttr = title ? ` title="${title}"` : '';
  return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`;
};

const renderMarkdown = (text: string) => {
  if (typeof text !== 'string') return '';
  const html = marked(text, { renderer }) as string;
  return DOMPurify.sanitize(html, { ADD_ATTR: ['target'] });
};
</script>

<style>
.duration-300 {
  animation-duration: .3s;
}

.duration-300 {
  transition-duration: .3s;
}
</style>
