<template>
  <div
    @click="handleSessionClick"
    class="group flex items-center rounded-[10px] cursor-pointer transition-colors w-full gap-[12px] h-[36px] flex-shrink-0 pointer-events-auto ps-[9px] pe-[2px] active:bg-[var(--fill-tsp-white-dark)]"
    :class="isCurrentSession ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">

    <!-- 状态图标 -->
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
        <img
          class="size-[18px] object-cover [filter:brightness(0)_saturate(100%)_invert(52%)_sepia(7%)_saturate(141%)_hue-rotate(349deg)_brightness(95%)_contrast(86%)]"
          :alt="session.title || ''"
          src="https://files.manuscdn.com/assets/icon/session/chatting.svg" />
      </template>
    
    </div>

    <!-- 标题 -->
    <div class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
      <span class="truncate" :title="session.title || t('New Chat')">
        {{ session.title || t('New Chat') }}
      </span>
    </div>

    <!-- 省略号菜单 -->
    <div class="shrink-0 flex items-center gap-1">
      <div
        @click.stop="handleSessionMenuClick"
        class="group-hover:flex hidden size-8 rounded-[8px] cursor-pointer items-center justify-center hover:bg-[var(--fill-tsp-white-light)]"
        :class="isContextMenuOpen ? '!flex bg-[var(--fill-tsp-white-light)]' : ''"
        aria-expanded="false" aria-haspopup="dialog">
        <Ellipsis :size="18" class="text-[var(--icon-tertiary)]" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ellipsis } from 'lucide-vue-next';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { ListSessionItem, SessionStatus } from '../types/response';
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
      })
    }
  }, (_: string) => {
    isContextMenuOpen.value = false;
  });
};
</script>