<template>
  <!-- User messages (right-aligned) -->
  <div v-if="content.role === 'user'" class="flex flex-col flex-wrap gap-2 items-end justify-end">
    <ChatAttachmentList :attachments="content.attachments" align-end />
  </div>

  <!-- Assistant messages (left-aligned) -->
  <div v-else class="flex flex-col flex-wrap gap-2 justify-start">
    <ChatAttachmentList
      :attachments="content.attachments"
      :show-all-files-button="!props.hideAllFilesButton"
      @show-all-files="showAllFiles"
    />
  </div>
</template>

<script setup lang="ts">
import type { AttachmentsContent } from '../types/message'
import { useSessionFileList } from '../composables/useSessionFileList'
import ChatAttachmentList from './ChatAttachmentList.vue'

const { showSessionFileList } = useSessionFileList()

const props = defineProps<{
  content: AttachmentsContent
  hideAllFilesButton?: boolean
}>()

const showAllFiles = () => {
  showSessionFileList()
}
</script>
