<template>
  <!-- Official PDF / HTML content often uses iframe full bleed -->
  <div class="flex-1 min-h-0 relative w-full h-full overflow-hidden flex flex-col">
    <iframe
      v-if="url"
      :src="url"
      class="w-full h-full border-0 bg-white"
      :title="file.filename || 'preview'"
    />
    <div
      v-else
      class="absolute inset-0 z-10 flex items-center justify-center bg-[var(--background-menu-white)] text-sm text-[var(--text-tertiary)]">
      {{ t('Loading...') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getFileDownloadUrl, type FileInfo } from '../../api/file'

const props = defineProps<{
  file: FileInfo
}>()

const { t } = useI18n()
const url = ref('')

watch(
  () => props.file,
  async (file) => {
    if (!file) return
    url.value = await getFileDownloadUrl(file)
  },
  { immediate: true },
)
</script>
