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
  <ToolUse v-else-if="message.type === 'tool'" :tool="toolContent" @click="handleToolClick(toolContent)" />
  <div v-else-if="message.type === 'step'" class="flex flex-col">
    <div class="text-sm w-full clickable flex gap-2 justify-between group/header truncate text-[var(--text-primary)]"
      data-event-id="HNtP7XOMUOhPemItd2EkK2">
      <div class="flex flex-row gap-2 justify-center items-center truncate">
        <div v-if="stepContent.status !== 'completed'"
          class="w-4 h-4 flex-shrink-0 flex items-center justify-center border border-[var(--border-dark)] rounded-[15px]">
        </div>
        <div v-else
          class="w-4 h-4 flex-shrink-0 flex items-center justify-center border-[var(--border-dark)] rounded-[15px] bg-[var(--text-disable)] dark:bg-[var(--fill-tsp-white-dark)] border-0">
          <CheckIcon class="text-[var(--icon-white)] dark:text-[var(--icon-white-tsp)]" :size="10" />
        </div>
        <div class="truncate font-medium markdown-content"
          v-html="stepContent.description ? renderMarkdown(stepContent.description) : ''">
        </div>
        <span class="flex-shrink-0 flex" @click="isExpanded = !isExpanded;">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-chevron-down transition-transform duration-300 w-4 h-4"
            :class="{ 'rotate-180': isExpanded }">
            <path d="m6 9 6 6 6-6"></path>
          </svg>
        </span>
      </div>
      <div class="float-right transition text-[12px] text-[var(--text-tertiary)] invisible group-hover/header:visible">
        {{ relativeTime(message.content.timestamp) }}
      </div>
    </div>
    <div class="flex">
      <div class="w-[24px] relative">
        <div class="border-l border-dashed border-[var(--border-dark)] absolute start-[8px] top-0 bottom-0"
          style="height: calc(100% + 14px);"></div>
      </div>
      <div
        class="flex flex-col gap-3 flex-1 min-w-0 overflow-hidden pt-2 transition-[max-height,opacity] duration-150 ease-in-out"
        :class="{ 'max-h-[100000px] opacity-100': isExpanded, 'max-h-0 opacity-0': !isExpanded }">
        <ToolUse v-for="(tool, index) in stepContent.tools" :key="index" :tool="tool" @click="handleToolClick(tool)" />
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
import { Message, MessageContent, AttachmentsContent } from '../types/message';
import ToolUse from './ToolUse.vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { CheckIcon } from 'lucide-vue-next';
import { computed, ref, type Component } from 'vue';
import { ToolContent, StepContent } from '../types/message';
import { useRelativeTime } from '../composables/useTime';
import { Bot } from 'lucide-vue-next';
import AttachmentsMessage from './AttachmentsMessage.vue';
import ChatMessageCopyButton from './ChatMessageCopyButton.vue';
import ChatAttachmentList from './ChatAttachmentList.vue';


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
}>();

const hideAssistantHeader = computed(() => props.hideHeader ?? false);
const showLiteBadge = computed(() => props.showLiteBadge ?? false);
const showCopyActions = computed(() => props.showCopyActions ?? false);
const isLastBeforeUser = computed(() => props.isLastBeforeUser ?? false);

const emit = defineEmits<{
  (e: 'toolClick', tool: ToolContent): void;
}>();

const handleToolClick = (tool: ToolContent) => {
  emit('toolClick', tool);
};

// For backward compatibility, provide the original computed properties
const stepContent = computed(() => props.message.content as StepContent);
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

// Control content expand/collapse state
const isExpanded = ref(true);

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
