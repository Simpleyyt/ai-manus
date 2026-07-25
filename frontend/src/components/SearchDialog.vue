<template>
  <div v-if="visible" class="absolute z-[1000] pointer-events-auto">
    <div
      class="w-full h-full bg-black/60 backdrop-blur-[4px] fixed inset-0"
      @click="emit('close')"
    />
    <div
      role="dialog"
      class="shadow-menu pointer-events-auto fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-w-[95%] max-h-[95%] overflow-hidden w-[680px] h-[440px] flex flex-col rounded-[20px] bg-[var(--background-menu-white)]"
      @keydown.escape.stop="emit('close')">
      <!-- Search header -->
      <h3 class="flex items-center gap-4 border-b border-b-[var(--border-main)] pt-5 pe-3 pb-[18px] ps-5 shrink-0">
        <Search :size="18" class="shrink-0" stroke="var(--icon-secondary)" />
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          class="overflow-hidden w-full disabled:cursor-not-allowed ring-inset focus:ring-[1px] focus:ring-[var(--border-dark)] flex-1 bg-transparent border-0 focus-visible:ring-0 outline-none px-0 py-0 h-auto rounded-none text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] text-[16px] font-normal leading-6"
          :placeholder="t('Search tasks...')"
          @keydown.enter.prevent="selectFirst"
        />
        <button
          type="button"
          class="flex h-7 w-7 items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-white-light)]"
          @click="emit('close')">
          <X class="size-5 text-[var(--icon-tertiary)]" />
        </button>
      </h3>

      <ul class="flex flex-1 flex-col overflow-auto pb-4 min-h-0">
        <!-- New Task -->
        <li
          class="mx-2 flex items-center gap-4 rounded-lg px-3 py-2 text-[var(--text-primary)] clickable cursor-pointer hover:bg-[var(--fill-tsp-white-light)] mt-[12px]"
          :class="highlightIndex === -1 ? 'bg-[var(--fill-tsp-white-light)]' : ''"
          @click="createNewTask"
          @mouseenter="highlightIndex = -1">
          <span class="flex h-[18px] w-[18px] shrink-0 items-center justify-center">
            <SquarePen :size="18" stroke="var(--icon-primary)" />
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex w-full items-center gap-2.5">
              <div class="flex min-w-0 flex-1 items-center gap-1.5">
                <span class="block min-w-0 truncate text-sm font-normal text-[var(--text-primary)]">
                  {{ t('New Task') }}
                </span>
              </div>
            </div>
          </div>
        </li>

        <template v-for="group in groupedSessions" :key="group.label">
          <li class="flex px-2.5 pb-1.5 font-medium text-[var(--text-tertiary)] !px-5 !pb-2 !pt-3 text-[13px]">
            {{ group.label }}
          </li>
          <li
            v-for="(session, idx) in group.items"
            :key="session.session_id"
            class="mx-2 flex items-center gap-4 rounded-lg px-3 py-2 text-[var(--text-primary)] clickable cursor-pointer hover:bg-[var(--fill-tsp-white-light)]"
            :class="flatIndex(group, idx) === highlightIndex ? 'bg-[var(--fill-tsp-white-light)]' : ''"
            @click="openSession(session.session_id)"
            @mouseenter="highlightIndex = flatIndex(group, idx)">
            <div class="relative h-[18px] w-[18px] shrink-0 flex items-center justify-center">
              <FileText :size="18" class="text-[var(--icon-tertiary)]" />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex w-full items-center gap-2.5">
                <div class="flex min-w-0 flex-1 items-center gap-1.5">
                  <span class="block min-w-0 truncate text-sm font-normal text-[var(--text-primary)]">
                    {{ session.title || t('New Chat') }}
                  </span>
                </div>
                <div
                  v-if="session.latest_message_at"
                  class="shrink-0 overflow-hidden truncate whitespace-nowrap text-end text-xs font-normal text-[var(--text-tertiary)]">
                  {{ formatTime(session.latest_message_at) }}
                </div>
              </div>
              <span
                v-if="session.latest_message"
                class="block truncate text-xs font-normal text-[var(--text-tertiary)]">
                {{ session.latest_message }}
              </span>
            </div>
          </li>
        </template>

        <li
          v-if="query.trim() && flatSessions.length === 0"
          class="px-5 py-8 text-center text-sm text-[var(--text-tertiary)]">
          {{ t('No matching tasks') }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileText, Search, SquarePen, X } from 'lucide-vue-next';
import { computed, nextTick, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { ListSessionItem } from '@/types/response';

const props = defineProps<{
  visible: boolean;
  sessions: ListSessionItem[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'new-task'): void;
}>();

const { t, locale } = useI18n();
const router = useRouter();
const inputRef = ref<HTMLInputElement | null>(null);
const query = ref('');
const highlightIndex = ref(-1);

const flatSessions = computed(() => {
  const q = query.value.trim().toLowerCase();
  let list = [...props.sessions].sort((a, b) => (b.latest_message_at || 0) - (a.latest_message_at || 0));
  if (q) {
    list = list.filter((s) => {
      const title = (s.title || '').toLowerCase();
      const msg = (s.latest_message || '').toLowerCase();
      return title.includes(q) || msg.includes(q);
    });
  }
  return list;
});

type Group = { label: string; items: ListSessionItem[]; startIndex: number };

const startOfDay = (d: Date) => {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x.getTime();
};

const groupedSessions = computed((): Group[] => {
  const now = new Date();
  const today = startOfDay(now);
  const yesterday = today - 86400000;
  const week = today - 7 * 86400000;
  const month = today - 30 * 86400000;

  const buckets: Record<string, ListSessionItem[]> = {
    today: [],
    yesterday: [],
    week: [],
    month: [],
    older: [],
  };

  for (const s of flatSessions.value) {
    const ts = (s.latest_message_at || 0) * (s.latest_message_at && s.latest_message_at < 1e12 ? 1000 : 1);
    if (!ts) {
      buckets.older.push(s);
      continue;
    }
    if (ts >= today) buckets.today.push(s);
    else if (ts >= yesterday) buckets.yesterday.push(s);
    else if (ts >= week) buckets.week.push(s);
    else if (ts >= month) buckets.month.push(s);
    else buckets.older.push(s);
  }

  const labels: [keyof typeof buckets, string][] = [
    ['today', t('Today')],
    ['yesterday', t('Yesterday')],
    ['week', t('Past 7 days')],
    ['month', t('Past 30 days')],
    ['older', t('Older')],
  ];

  const groups: Group[] = [];
  let start = 0;
  for (const [key, label] of labels) {
    const items = buckets[key];
    if (!items.length) continue;
    groups.push({ label, items, startIndex: start });
    start += items.length;
  }
  return groups;
});

const flatIndex = (group: Group, idx: number) => group.startIndex + idx;

const formatTime = (raw: number) => {
  const ts = raw < 1e12 ? raw * 1000 : raw;
  const d = new Date(ts);
  const now = new Date();
  const today = startOfDay(now);
  const yesterday = today - 86400000;
  const timeStr = d.toLocaleTimeString(locale.value === 'zh' ? 'zh-CN' : 'en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: false,
  });

  if (ts >= today) return timeStr;
  if (ts >= yesterday) return `${t('Yesterday')} ${timeStr}`;

  const weekAgo = today - 7 * 86400000;
  if (ts >= weekAgo) {
    const weekday = d.toLocaleDateString(locale.value === 'zh' ? 'zh-CN' : 'en-US', { weekday: 'short' });
    return `${weekday} ${timeStr}`;
  }
  return d.toLocaleDateString(locale.value === 'zh' ? 'zh-CN' : 'en-US', {
    month: 'short',
    day: 'numeric',
  });
};

const openSession = (sessionId: string) => {
  emit('close');
  router.push(`/chat/${sessionId}`);
};

const createNewTask = () => {
  emit('close');
  emit('new-task');
};

const selectFirst = () => {
  if (highlightIndex.value === -1) {
    createNewTask();
    return;
  }
  const s = flatSessions.value[highlightIndex.value];
  if (s) openSession(s.session_id);
};

watch(
  () => props.visible,
  async (v) => {
    if (v) {
      query.value = '';
      highlightIndex.value = -1;
      await nextTick();
      inputRef.value?.focus();
    }
  },
);
</script>
