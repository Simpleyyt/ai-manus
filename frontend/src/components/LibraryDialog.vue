<template>
  <div v-if="visible" class="absolute z-[1000] pointer-events-auto">
    <div
      class="w-full h-full bg-black/60 backdrop-blur-[4px] fixed inset-0"
      @click="emit('close')"
    />
    <div
      role="dialog"
      class="bg-[var(--background-menu-white)] rounded-[20px] border border-white/5 fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-w-[95%] max-h-[85%] overflow-hidden w-[520px] flex flex-col">
      <div class="pt-5 pb-[10px] px-5 flex items-center justify-between">
        <h3 class="text-[var(--text-primary)] text-[18px] leading-[24px] font-semibold">
          {{ t('Library') }}
        </h3>
        <button
          type="button"
          class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
          @click="emit('close')">
          <X :size="18" class="text-[var(--icon-tertiary)]" />
        </button>
      </div>
      <div class="px-5 pb-5 overflow-y-auto min-h-0 flex-1">
        <div v-if="loading" class="py-10 text-center text-sm text-[var(--text-tertiary)]">
          {{ t('Loading...') }}
        </div>
        <div v-else-if="files.length === 0" class="py-10 text-center text-sm text-[var(--text-tertiary)]">
          {{ t('No files in library') }}
        </div>
        <div v-else class="flex flex-col gap-1">
          <button
            v-for="(file, idx) in files"
            :key="`${file.session_id}-${file.file_id || idx}`"
            type="button"
            class="flex items-center gap-3 rounded-[10px] px-3 py-2 text-left hover:bg-[var(--fill-tsp-white-main)]"
            @click="openSession(file.session_id)">
            <FileText :size="18" class="shrink-0 text-[var(--icon-tertiary)]" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-[14px] text-[var(--text-primary)]">
                {{ file.filename || file.file_path || t('Untitled') }}
              </div>
              <div class="truncate text-[12px] text-[var(--text-tertiary)]">
                {{ file.session_title || t('New Chat') }}
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileText, X } from 'lucide-vue-next';
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { getLibraryFiles } from '../api/project';
import { LibraryFileItem } from '../types/response';

const props = defineProps<{ visible: boolean }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const { t } = useI18n();
const router = useRouter();
const files = ref<LibraryFileItem[]>([]);
const loading = ref(false);

const load = async () => {
  loading.value = true;
  try {
    const res = await getLibraryFiles();
    files.value = res.files;
  } catch (e) {
    console.error(e);
    files.value = [];
  } finally {
    loading.value = false;
  }
};

watch(() => props.visible, (v) => {
  if (v) load();
});

const openSession = (sessionId: string) => {
  emit('close');
  router.push(`/chat/${sessionId}`);
};
</script>
