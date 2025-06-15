<template>
  <div class="px-2">
    <div @click="handleSessionClick"
      class="group flex h-14 cursor-pointer items-center gap-2 rounded-[10px] px-2 transition-colors"
      :class="isCurrentSession ? 'bg-[var(--background-white-main)]' : 'hover:bg-[var(--fill-tsp-gray-main)]'">
      <div class="relative">
        <div class="h-8 w-8 rounded-full flex items-center justify-center relative bg-[var(--fill-tsp-white-dark)]">
          <div class="relative h-4 w-4 object-cover brightness-0 opacity-75 dark:opacity-100 dark:brightness-100">
            <img alt="Hello" class="w-full h-full object-cover" src="/chatting.svg">
          </div>
        </div>
        <div v-if="session.status === SessionStatus.RUNNING || session.status === SessionStatus.PENDING"
          class="absolute -start-[5px] -top-[3px] w-[calc(100%+8px)] h-[calc(100%+8px)]"
          style="transform: rotateY(180deg);">
          <SpinnigIcon />
        </div>
        <div v-if="session.unread_message_count > 0 && !isCurrentSession"
          class="flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[var(--function-error)] absolute -end-1 -top-1">
          <span class="px-1 text-xs text-[var(--text-white)]">{{ session.unread_message_count }}</span>
        </div>
      </div>
      <div class="min-w-20 flex-1 transition-opacity opacity-100">
        <div class="flex items-center gap-1 overflow-x-hidden">
          <span class="truncate text-sm font-medium text-[var(--text-primary)] flex-1 min-w-0"
            :title="session.title || t('New Chat')">
            <span class="">
              {{ session.title || t('New Chat') }}
            </span>
          </span>
          <span class="text-[var(--text-tertiary)] text-xs whitespace-nowrap">
            {{ session.latest_message_at ? customTime(session.latest_message_at) : '' }}
          </span>
        </div>
        <div class="flex items-center gap-2 h-[18px] relative">
          <span class="min-w-0 flex-1 truncate text-xs text-[var(--text-tertiary)]"
            :title="session.latest_message || ''">
            {{ session.latest_message }}
          </span>
          <div @click="handleSessionMenuClick"
            class="w-[22px] h-[22px] flex rounded-[6px] items-center justify-center pointer cursor-pointer border border-[var(--border-main)] shadow-sm group-hover:visible touch-device:visible"
            :class="!isContextMenuOpen ? 'invisible bg-[var(--background-menu-white)]' : 'visible bg-[var(--fill-tsp-gray-dark)]'"
            aria-expanded="false" aria-haspopup="dialog">
            <Ellipsis :size="16" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ellipsis } from 'lucide-vue-next';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useCustomTime } from '../composables/useTime';
import { ListSessionItem, SessionStatus } from '../types/response';
import SpinnigIcon from './icons/SpinnigIcon.vue';
import { useContextMenu, createDangerMenuItem } from '../composables/useContextMenu';
import { useDialog } from '../composables/useDialog';
import { deleteSession } from '../api/agent';
import { showSuccessToast, showErrorToast } from '../utils/toast';
import { Trash } from 'lucide-vue-next';

interface Props {
  session: ListSessionItem;
}

const props = defineProps<Props>();

const { t } = useI18n();
const { customTime } = useCustomTime();
const route = useRoute();
const router = useRouter();
const { showContextMenu } = useContextMenu();
const { showConfirmDialog } = useDialog();
const isContextMenuOpen = ref(false);

const emit = defineEmits<{
  (e: 'deleted', sessionId: string): void
}>();

const currentSessionId = computed(() => {
  return route.params.sessionId as string;
});

const isCurrentSession = computed(() => {
  return currentSessionId.value === props.session.session_id;
});

const handleSessionClick = () => {
  router.push(`/chat/${props.session.session_id}`);
};

const handleSessionMenuClick = (event: MouseEvent) => {
  event.stopPropagation();

  const target = event.currentTarget as HTMLElement;
  isContextMenuOpen.value = true;

  showContextMenu(props.session.session_id, target, [
    createDangerMenuItem('delete', t('Delete'), { icon: Trash }),
  ], (itemKey: string, _: string) => {
    if (itemKey === 'delete') {
      showConfirmDialog({
        title: t('Are you sure you want to delete this session?'),
        content: t('The chat history of this session cannot be recovered after deletion.'),
        confirmText: t('Delete'),
        cancelText: t('Cancel'),
        confirmType: 'danger',
        onConfirm: () => {
          emit('deleted', props.session.session_id);
          deleteSession(props.session.session_id).then(() => {
            showSuccessToast(t('Deleted successfully'));
          }).catch(() => {
            showErrorToast(t('Failed to delete session'));
          });
          if (isCurrentSession.value) {
            router.push('/');
          }
        }
      })
    }
  }, (_: string) => {
    isContextMenuOpen.value = false;
  });
};
</script>