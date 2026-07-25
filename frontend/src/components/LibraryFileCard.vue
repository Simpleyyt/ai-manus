<template>
  <!-- Official eR grid card (2930l2ba6yrcn.js) -->
  <div
    v-if="viewMode === 'grid'"
    role="button"
    tabindex="0"
    class="clickable relative flex cursor-pointer flex-col overflow-hidden rounded-[12px] border-[0.5px] border-[var(--border-dark)] bg-[var(--background-menu-white)] group hover:shadow-[0_7px_16px_0_var(--shadow-S)] text-left w-full"
    @click="emit('open')"
    @keydown.enter="emit('open')">
    <div class="flex items-center gap-2 px-2 py-[10px] relative border-b border-[var(--border-main)]">
      <div class="flex items-center justify-center flex-shrink-0 [&_svg]:w-6 [&_svg]:h-6">
        <component :is="fileType.icon" />
      </div>
      <div class="flex flex-1 min-w-0 items-center gap-1">
        <!-- Official ey: basename + ext inline flex, single text-sm truncate row -->
        <div class="min-w-0 flex-1 truncate text-[var(--text-primary)] text-sm" :title="displayName">
          <div class="flex min-w-0 max-w-full">
            <span class="truncate min-w-0">{{ baseName }}</span>
            <span v-if="extDot" class="flex-shrink-0">{{ extDot }}</span>
          </div>
        </div>
        <Star
          v-if="file.is_favorite"
          :size="16"
          class="flex-shrink-0"
          color="var(--function-warning)"
          fill="var(--function-warning)"
        />
      </div>
      <div class="flex items-center flex-shrink-0">
        <!-- Official ef FileActionsDropdown -->
        <button
          type="button"
          class="flex size-7 items-center justify-center rounded-md text-[var(--icon-tertiary)] hover:bg-[var(--fill-tsp-gray-main)]"
          :class="menuOpen ? 'bg-[var(--fill-tsp-gray-main)]' : ''"
          :title="t('More options')"
          @click.stop="openMenu">
          <Ellipsis :size="16" />
        </button>
      </div>
    </div>

    <!-- Official: aspect-[16/9] — preview canvas + hover action (Preview/Visit/Locate) -->
    <div class="aspect-[16/9] overflow-hidden relative bg-[var(--background-menu-white)]">
      <img
        v-if="previewKind === 'image' && previewUrl"
        :src="previewUrl"
        :alt="displayName"
        class="h-full w-full bg-[var(--fill-tsp-gray-dark)] object-top object-cover"
      />
      <div
        v-else-if="previewKind === 'text' && previewHtml"
        class="size-full p-[12px] relative"
        :style="{ background: isDark ? '#1c1c1c' : '#F7F7F7' }">
        <div class="scale-[0.8] origin-top-left">
          <pre
            class="library-code-preview m-0 w-[125%] h-[125%] text-[12px] leading-[16px] font-mono overflow-hidden whitespace-pre"
            v-html="previewHtml"
          />
        </div>
        <div
          class="pointer-events-none absolute left-0 right-0 bottom-0 h-[32px]"
          :style="{ background: codeFade }"
        />
      </div>
      <div
        v-else
        class="flex h-full w-full items-center justify-center bg-[var(--fill-tsp-white-main)]">
        <div class="[&_svg]:w-16 [&_svg]:h-16 opacity-90">
          <component :is="fileType.icon" />
        </div>
      </div>

      <!-- Official K.IconButton: absolute bottom-2 start-2, hidden until group-hover -->
      <button
        type="button"
        class="absolute bottom-2 start-2 z-20 size-7 rounded-[8px] items-center justify-center transition-opacity group-hover:pointer-events-auto group-hover:flex hidden bg-[var(--background-mask-black)] hover:opacity-80 hover:bg-[var(--background-mask-black)]"
        :title="hoverActionTitle"
        @click.stop="onHoverAction">
        <component
          :is="hoverActionIcon"
          class="size-4 text-[var(--icon-white)]"
          :size="16"
        />
      </button>
    </div>
  </div>

  <!-- Official eD list row -->
  <div
    v-else
    role="button"
    tabindex="0"
    class="clickable group flex cursor-pointer items-center hover:bg-[var(--fill-tsp-white-light)] md:w-[calc(100%+24px)] md:px-[12px] md:-ms-[12px] rounded-lg text-left"
    @click="emit('open')"
    @keydown.enter="emit('open')">
    <div
      class="w-full flex items-center border-b border-[var(--border-main)] gap-10 py-[12px] md:ps-[8px]">
      <div class="flex flex-1 min-w-0 items-center gap-3">
        <div class="flex-shrink-0 [&_svg]:w-6 [&_svg]:h-6">
          <component :is="fileType.icon" />
        </div>
        <div class="flex flex-1 min-w-0 items-center">
          <span class="min-w-0 truncate text-[14px] leading-[20px] text-[var(--text-primary)]">
            {{ displayName }}
          </span>
          <Star
            v-if="file.is_favorite"
            :size="16"
            class="flex-shrink-0 ms-1"
            color="var(--function-warning)"
            fill="var(--function-warning)"
          />
        </div>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0">
        <!-- Official eD hover action (group-hover); local always on — no select mode -->
        <button
          type="button"
          class="clickable size-7 flex items-center justify-center rounded-md pointer-events-none opacity-0 transition-opacity group-hover:pointer-events-auto group-hover:opacity-100 hover:bg-[var(--fill-tsp-white-main)]"
          :title="hoverActionTitle"
          @click.stop="onHoverAction">
          <component
            :is="hoverActionIcon"
            class="size-4 text-[var(--icon-secondary)]"
            :size="16"
          />
        </button>
        <button
          type="button"
          class="flex size-7 shrink-0 items-center justify-center rounded-md text-[var(--icon-secondary)] hover:bg-[var(--fill-tsp-white-main)]"
          :class="menuOpen ? 'opacity-100 bg-[var(--fill-tsp-white-main)]' : 'opacity-0 group-hover:opacity-100'"
          :title="t('More options')"
          @click.stop="openMenu">
          <Ellipsis :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ellipsis, Eye, ExternalLink, MessageSquarePlus, SquareArrowOutUpRight, Star } from 'lucide-vue-next';
import { computed, onMounted, ref, type Component } from 'vue';
import { useI18n } from 'vue-i18n';
import { downloadFile, getFileDownloadUrl, type FileInfo } from '../api/file';
import { createMenuItem, useContextMenu } from '../composables/useContextMenu';
import type { LibraryFileItem } from '../types/response';
import { getFileType } from '../utils/fileType';
import { highlightLibraryPreview } from '../utils/libraryHighlight';

type HoverAction = 'preview' | 'visit' | 'locate';

const props = defineProps<{
  file: LibraryFileItem;
  viewMode: 'grid' | 'list';
}>();

const emit = defineEmits<{
  (e: 'open'): void
  (e: 'locate'): void
  (e: 'favorite', isFavorite: boolean): void
  (e: 'send'): void
}>();

const { t } = useI18n();
const { showContextMenu } = useContextMenu();
const menuOpen = ref(false);

const previewUrl = ref<string | null>(null);
const previewHtml = ref<string | null>(null);
const previewKind = ref<'image' | 'text' | 'none'>('none');

const displayName = computed(() => props.file.filename || props.file.file_path || t('Untitled'));

const ext = computed(() => {
  const name = displayName.value;
  const i = name.lastIndexOf('.');
  if (i <= 0 || i === name.length - 1) return '';
  return name.slice(i + 1).toLowerCase();
});

const baseName = computed(() => {
  const name = displayName.value;
  const i = name.lastIndexOf('.');
  if (i <= 0) return name;
  return name.slice(0, i);
});

const extDot = computed(() => (ext.value ? `.${ext.value}` : ''));

const fileType = computed(() => getFileType(displayName.value));

const isDark = computed(() => document.documentElement.classList.contains('dark'));

const codeFade = computed(() =>
  isDark.value
    ? 'linear-gradient(180deg, #1c1c1c00 0%, #1c1c1cFF 100%)'
    : 'linear-gradient(180deg, #F7F7F700 0%, #F7F7F7FF 100%)',
);

const isImage = computed(() => {
  const ct = props.file.content_type || '';
  if (ct.startsWith('image/')) return true;
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'].includes(ext.value);
});

const isTextLike = computed(() => {
  const ct = props.file.content_type || '';
  if (ct.startsWith('text/') || ct.includes('json') || ct.includes('javascript') || ct.includes('xml')) {
    return true;
  }
  return [
    'py', 'js', 'ts', 'jsx', 'tsx', 'vue', 'java', 'c', 'cpp', 'go', 'rs', 'php',
    'rb', 'swift', 'kt', 'css', 'scss', 'html', 'xml', 'json', 'yaml', 'yml',
    'sql', 'toml', 'ini', 'md', 'txt', 'sh', 'bash',
  ].includes(ext.value);
});

const canSendToManus = computed(() => !!props.file.file_id);

/**
 * Official libraryUtils.getLibraryAttachmentHoverAction:
 * non-WEBDEV → preview; WEBDEV + url → visit; else locate.
 * Local library items are session files (no WEBDEV) → preview.
 */
const hoverAction = computed<HoverAction>(() => 'preview');

const hoverActionTitle = computed(() => {
  if (hoverAction.value === 'visit') return t('Visit');
  if (hoverAction.value === 'locate') return t('Locate in new tab');
  return t('Preview');
});

const hoverActionIcon = computed<Component>(() =>
  hoverAction.value === 'preview' ? Eye : SquareArrowOutUpRight,
);

const onHoverAction = () => {
  if (hoverAction.value === 'visit') {
    // Reserved for WEBDEV/website attachments with external URL
    return;
  }
  if (hoverAction.value === 'locate') {
    const sid = props.file.session_id;
    if (sid) window.open(`/chat/${sid}`, '_blank', 'noopener,noreferrer');
    return;
  }
  emit('open');
};

const openMenu = (event: MouseEvent) => {
  const target = event.currentTarget as HTMLElement;
  menuOpen.value = true;
  const favorited = !!props.file.is_favorite;

  const items = [
    createMenuItem('locate', t('Locate in task'), { icon: ExternalLink }),
    createMenuItem('favorite', favorited ? t('Unfavorite') : t('Add to favorites'), { icon: Star }),
  ];
  if (canSendToManus.value) {
    items.push(createMenuItem('send', t('Send to Manus'), { icon: MessageSquarePlus }));
  }

  const menuId = props.file.file_id || `${props.file.session_id}:${displayName.value}`;
  showContextMenu(menuId, target, items, async (itemKey: string) => {
    if (itemKey === 'locate') emit('locate');
    else if (itemKey === 'favorite') emit('favorite', !favorited);
    else if (itemKey === 'send') emit('send');
  }, () => {
    menuOpen.value = false;
  });
};

onMounted(async () => {
  const fileId = props.file.file_id;
  if (!fileId) return;
  try {
    if (isImage.value) {
      const info: FileInfo = {
        file_id: fileId,
        filename: displayName.value,
        content_type: props.file.content_type || undefined,
        upload_date: props.file.upload_date || '',
      };
      previewUrl.value = await getFileDownloadUrl(info);
      previewKind.value = 'image';
      return;
    }
    if (isTextLike.value && (props.file.size == null || props.file.size < 200_000)) {
      const blob = await downloadFile(fileId);
      const text = await blob.text();
      previewHtml.value = highlightLibraryPreview(text.slice(0, 1600), ext.value);
      previewKind.value = 'text';
    }
  } catch {
    previewKind.value = 'none';
  }
});
</script>

<style scoped>
/* Closer to official Code theme: keywords reddish */
.library-code-preview :deep(.tok-kw) {
  color: #cf222e;
}
.library-code-preview :deep(.tok-str) {
  color: #0a3069;
}
.library-code-preview :deep(.tok-cmt) {
  color: #6e7781;
}
.library-code-preview :deep(.tok-num) {
  color: #0550ae;
}

:global(.dark) .library-code-preview :deep(.tok-kw) {
  color: #ff7b72;
}
:global(.dark) .library-code-preview :deep(.tok-str) {
  color: #a5d6ff;
}
:global(.dark) .library-code-preview :deep(.tok-cmt) {
  color: #8b949e;
}
:global(.dark) .library-code-preview :deep(.tok-num) {
  color: #79c0ff;
}
</style>
