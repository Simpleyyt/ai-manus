<template>
  <!-- Official bz (project view) vs sidebar session row -->
  <div
    v-if="variant === 'project'"
    class="session-item px-2 mx-[-8px] w-[calc(100%+16px)] py-[12px] flex items-center gap-[12px] rounded-[8px] hover:bg-[var(--fill-tsp-white-light)] relative group cursor-pointer"
    :class="[
      isCurrentSession ? 'bg-[var(--fill-tsp-white-main)]' : '',
      isContextMenuOpen ? 'bg-[var(--fill-tsp-white-light)]' : '',
    ]"
    @click="handleSessionClick">
    <div class="flex items-center justify-center size-[18px] flex-shrink-0">
      <template v-if="session.status === SessionStatus.RUNNING || session.status === SessionStatus.PENDING">
        <div
          class="border rounded-full animate-spin"
          style="width: 18px; height: 18px; border-width: 2px; border-color: var(--fill-blue); border-top-color: var(--icon-brand);"
        />
      </template>
      <template v-else-if="session.status === SessionStatus.WAITING">
        <svg height="18" width="18" fill="none" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
          <g clip-path="url(#waiting-clip-project)">
            <circle cx="8" cy="8" r="6.5" stroke="var(--function-warning)" stroke-dasharray="2.44 1.62" stroke-width="1.5" />
          </g>
          <defs><clipPath id="waiting-clip-project"><rect height="16" width="16" fill="white" /></clipPath></defs>
        </svg>
      </template>
      <template v-else>
        <FileText :size="18" class="text-[var(--icon-tertiary)] flex-shrink-0" />
      </template>
    </div>

    <div class="flex flex-1 min-w-0 gap-[6px] items-center">
      <span
        class="text-sm font-normal min-w-0 truncate text-[var(--text-primary)]"
        :title="session.title || t('Untitled')">
        {{ session.title || t('Untitled') }}
      </span>
      <Star
        v-if="session.is_favorite && !hasUnread"
        :size="16"
        class="flex-shrink-0 text-[var(--function-warning)]"
        fill="var(--function-warning)"
      />
    </div>

    <div class="relative h-[28px] flex items-center flex-shrink-0">
      <div
        class="flex items-center flex-shrink-0 gap-[12px] opacity-100 group-hover:opacity-0 pe-[6px]"
        :class="isContextMenuOpen ? 'opacity-0' : ''">
        <span
          v-if="timeLabel"
          class="text-[var(--text-tertiary)] text-xs"
          :title="timeFullLabel">
          {{ timeLabel }}
        </span>
        <div
          v-if="hasUnread"
          class="flex items-center justify-center min-w-[18px] h-[18px] rounded-full bg-[var(--function-error)] px-[4px]">
          <span class="text-[11px] text-[var(--text-white)] leading-none">
            {{ unreadBadge }}
          </span>
        </div>
      </div>
      <div
        class="absolute top-0 end-0 group-hover:opacity-100 group-hover:z-10 opacity-0"
        :class="isContextMenuOpen ? 'opacity-100 z-10' : ''">
        <button
          type="button"
          class="flex size-[28px] items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-light)]"
          :class="isContextMenuOpen ? 'bg-[var(--fill-tsp-gray-main)]' : ''"
          :title="t('More options')"
          @click="handleSessionMenuClick">
          <Ellipsis :size="18" class="text-[var(--icon-tertiary)]" />
        </button>
      </div>
    </div>

    <div
      class="h-[1px] bg-[var(--border-light)] -bottom-[0.5px] absolute start-[10px] end-[8px] group-hover:opacity-0 [.session-item:has(+.session-item:hover)_&]:opacity-0"
    />
  </div>

  <div
    v-else
    @click="handleSessionClick"
    class="group flex items-center rounded-[10px] cursor-pointer transition-colors w-full gap-[8px] h-[36px] flex-shrink-0 pointer-events-auto ps-[8px] pe-[2px] active:bg-[var(--fill-tsp-white-dark)]"
    :class="[
      isCurrentSession ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]',
      rowClass,
    ]">

    <div class="shrink-0 size-[18px] flex items-center justify-center relative">
      <template v-if="session.status === SessionStatus.RUNNING || session.status === SessionStatus.PENDING">
        <div class="border rounded-full animate-spin" style="width: 18px; height: 18px; border-width: 2px; border-color: var(--fill-blue); border-top-color: var(--icon-brand);"></div>
      </template>
      <template v-else-if="session.status === SessionStatus.WAITING">
        <svg height="18" width="18" fill="none" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
          <g clip-path="url(#waiting-clip)">
            <circle cx="8" cy="8" r="6.5" stroke="var(--function-warning)" stroke-dasharray="2.44 1.62" stroke-width="1.5"></circle>
          </g>
          <defs><clipPath id="waiting-clip"><rect height="16" width="16" fill="white"></rect></clipPath></defs>
        </svg>
      </template>
      <template v-else>
        <FileText :size="18" class="text-[var(--icon-tertiary)]" />
      </template>
    </div>

    <div class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
      <span
        class="truncate"
        :class="hasUnread ? 'font-semibold' : 'font-normal'"
        :title="session.title || t('New Chat')">
        {{ session.title || t('New Chat') }}
      </span>
      <Star
        v-if="session.is_favorite"
        :size="12"
        class="shrink-0 text-[var(--function-warning)]"
        fill="var(--function-warning)" />
    </div>

    <div class="shrink-0 flex items-center gap-1">
      <div
        @click.stop="handleSessionMenuClick"
        class="group-hover:flex hidden size-8 rounded-[8px] cursor-pointer items-center justify-center hover:bg-[var(--fill-tsp-white-light)]"
        :class="isContextMenuOpen ? '!flex bg-[var(--fill-tsp-white-light)]' : ''"
        :title="t('More options')"
        aria-expanded="false" aria-haspopup="dialog">
        <Ellipsis :size="18" class="text-[var(--icon-tertiary)]" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ellipsis, FileText, Trash, Share2, Pencil, Star, ExternalLink, FolderPlus, Folder, FolderSync, Pin } from 'lucide-vue-next';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { ListSessionItem, SessionStatus, ProjectItem } from '../types/response';
import { useContextMenu, createDangerMenuItem, createMenuItem, createSeparator, createSubmenuItem } from '../composables/useContextMenu';
import { useDialog } from '../composables/useDialog';
import {
  deleteSession,
  shareSession,
  updateSessionTitle,
  favoriteSession,
  unfavoriteSession,
  pinSession,
  moveSessionProject,
} from '../api/agent';
import { createProject } from '../api/project';
import { showSuccessToast, showErrorToast } from '../utils/toast';
import { formatCustomTime } from '../utils/time';
import { eventBus } from '../utils/eventBus';

interface Props {
  session: ListSessionItem;
  projects?: ProjectItem[];
  /** Official bz row on project page vs compact sidebar row */
  variant?: 'sidebar' | 'project';
  /** Extra classes for nested project tasks (official ps-[24px]) */
  rowClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  projects: () => [],
  variant: 'sidebar',
  rowClass: '',
});

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const { showContextMenu } = useContextMenu();
const { showConfirmDialog, showInputDialog } = useDialog();
const isContextMenuOpen = ref(false);

const emit = defineEmits<{
  (e: 'deleted', sessionId: string): void
  (e: 'renamed', sessionId: string, title: string): void
  (e: 'shared', sessionId: string): void
  (e: 'favorited', sessionId: string, isFavorite: boolean): void
  (e: 'pinned', sessionId: string, isPinned: boolean): void
  (e: 'moved', sessionId: string, projectId: string | null): void
}>();

const currentSessionId = computed(() => route.params.sessionId as string);
const isCurrentSession = computed(() => currentSessionId.value === props.session.session_id);

const hasUnread = computed(() => {
  const active = props.session.status === SessionStatus.RUNNING
    || props.session.status === SessionStatus.PENDING
    || props.session.status === SessionStatus.WAITING;
  return !active && (props.session.unread_message_count ?? 0) > 0;
});

const unreadBadge = computed(() => {
  const n = props.session.unread_message_count ?? 0;
  return n > 99 ? '99+' : String(n);
});

const timeLabel = computed(() => {
  const ts = props.session.latest_message_at;
  if (!ts) return '';
  return formatCustomTime(ts, t, locale.value);
});

const timeFullLabel = computed(() => {
  const ts = props.session.latest_message_at;
  if (!ts) return '';
  return new Date(ts * 1000).toLocaleString(locale.value);
});

const handleSessionClick = () => {
  router.push(`/chat/${props.session.session_id}`);
};

const handleSessionMenuClick = (event: MouseEvent) => {
  event.stopPropagation();
  const target = event.currentTarget as HTMLElement;
  isContextMenuOpen.value = true;
  const favoritedNow = !!props.session.is_favorite;
  const pinnedNow = !!props.session.is_pinned;

  const items = [
    createMenuItem('share', t('Share'), { icon: Share2 }),
    createMenuItem('rename', t('Rename'), { icon: Pencil }),
    createMenuItem('open', t('Open in new tab'), { icon: ExternalLink }),
  ];

  // Official: single「移动到项目」row → submenu (新项目 / projects)
  const moveChildren = [
    createMenuItem('new_project', t('New project'), { icon: FolderPlus }),
    createSeparator(),
    ...props.projects.map((project) =>
      createMenuItem(`move:${project.project_id}`, project.name, {
        icon: Folder,
        checked: project.project_id === props.session.project_id,
      }),
    ),
  ];
  if (props.session.project_id) {
    moveChildren.push(createSeparator());
    moveChildren.push(createMenuItem('remove_project', t('Remove from project'), { icon: Folder }));
  }
  items.push(createSubmenuItem('move_project', t('Move to project'), moveChildren, { icon: FolderSync }));

  items.push(createSeparator());
  items.push(createMenuItem('pin', pinnedNow ? t('Unpin') : t('Pin'), { icon: Pin }));
  items.push(createMenuItem('favorite', favoritedNow ? t('Unfavorite') : t('Add to favorites'), { icon: Star }));
  items.push(createDangerMenuItem('delete', t('Delete'), { icon: Trash }));

  showContextMenu(props.session.session_id, target, items, async (itemKey: string) => {
    if (itemKey === 'share') {
      try {
        await shareSession(props.session.session_id);
        const url = `${window.location.origin}/share/${props.session.session_id}`;
        try {
          await navigator.clipboard.writeText(url);
          showSuccessToast(t('Link copied to clipboard'));
        } catch {
          showSuccessToast(t('Share Instantly'));
        }
        emit('shared', props.session.session_id);
      } catch {
        showErrorToast(t('Failed to share session'));
      }
    } else if (itemKey === 'rename') {
      showInputDialog({
        title: t('Rename'),
        initialValue: props.session.title || '',
        placeholder: t('Enter task name'),
        confirmText: t('Save'),
        onConfirm: async (value: string) => {
          if (!value) return;
          try {
            const result = await updateSessionTitle(props.session.session_id, value);
            emit('renamed', props.session.session_id, result.title);
            showSuccessToast(t('Renamed successfully'));
          } catch {
            showErrorToast(t('Failed to rename session'));
          }
        }
      });
    } else if (itemKey === 'pin') {
      try {
        const result = await pinSession(props.session.session_id, !pinnedNow);
        emit('pinned', props.session.session_id, result.is_pinned);
        showSuccessToast(result.is_pinned ? t('Task pinned') : t('Task unpinned'));
      } catch {
        showErrorToast(t('Failed to update pin'));
      }
    } else if (itemKey === 'favorite') {
      try {
        const result = favoritedNow
          ? await unfavoriteSession(props.session.session_id)
          : await favoriteSession(props.session.session_id);
        emit('favorited', props.session.session_id, result.is_favorite);
        showSuccessToast(result.is_favorite ? t('Added to favorite') : t('Removed from favorite'));
      } catch {
        showErrorToast(t('Failed to update favorite'));
      }
    } else if (itemKey === 'open') {
      window.open(`/chat/${props.session.session_id}`, '_blank');
    } else if (itemKey === 'new_project') {
      showInputDialog({
        title: t('New project'),
        placeholder: t('Enter project name'),
        confirmText: t('Create'),
        onConfirm: async (value: string) => {
          if (!value) return;
          try {
            const project = await createProject(value);
            await moveSessionProject(props.session.session_id, project.project_id);
            emit('moved', props.session.session_id, project.project_id);
            eventBus.emit('projects:changed');
            showSuccessToast(t('Moved to project'));
          } catch {
            showErrorToast(t('Failed to create project'));
          }
        },
      });
    } else if (itemKey.startsWith('move:')) {
      const projectId = itemKey.slice(5);
      if (projectId === props.session.project_id) return;
      try {
        await moveSessionProject(props.session.session_id, projectId);
        emit('moved', props.session.session_id, projectId);
        showSuccessToast(t('Moved to project'));
      } catch {
        showErrorToast(t('Failed to move session'));
      }
    } else if (itemKey === 'remove_project') {
      try {
        await moveSessionProject(props.session.session_id, null);
        emit('moved', props.session.session_id, null);
        showSuccessToast(t('Removed from project'));
      } catch {
        showErrorToast(t('Failed to move session'));
      }
    } else if (itemKey === 'delete') {
      showConfirmDialog({
        title: t('Delete this task?'),
        content: t('The chat history of this session cannot be recovered after deletion.'),
        confirmText: t('Delete'),
        cancelText: t('Cancel'),
        confirmType: 'danger',
        onConfirm: () => {
          deleteSession(props.session.session_id).then(() => {
            showSuccessToast(t('Deleted successfully'));
            emit('deleted', props.session.session_id);
          }).catch(() => {
            showErrorToast(t('Failed to delete session'));
          });
          if (isCurrentSession.value) {
            router.push('/');
          }
        }
      });
    }
  }, () => {
    isContextMenuOpen.value = false;
  });
};
</script>
