<template>
  <div v-if="visible" class="absolute z-[1000] pointer-events-auto">
    <div class="w-full h-full bg-black/60 backdrop-blur-[4px] fixed inset-0" @click="emit('close')" />
    <div
      role="dialog"
      class="bg-[var(--background-menu-white)] rounded-[20px] border border-white/5 fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-w-[95%] w-[440px] overflow-hidden flex flex-col shadow-[0px_8px_32px_0px_var(--shadow-S)]">
      <div class="pt-5 pb-[10px] px-5 flex items-center justify-between">
        <h3 class="text-[var(--text-primary)] text-[18px] leading-[24px] font-semibold">
          {{ t('Collaborate') }}
        </h3>
        <button
          type="button"
          class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
          @click="emit('close')">
          <X :size="18" class="text-[var(--icon-tertiary)]" />
        </button>
      </div>

      <div class="px-5 pb-5 flex flex-col gap-4">
        <p class="text-[13px] text-[var(--text-tertiary)]">
          {{ t('Invite others to this task. Collaborators can view and prompt together.') }}
        </p>

        <div class="flex gap-2">
          <input
            v-model="email"
            type="email"
            class="flex-1 h-10 rounded-[10px] border border-[var(--border-main)] bg-transparent px-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disable)] outline-none focus:border-[var(--border-dark)]"
            :placeholder="t('Email address')"
            @keydown.enter.prevent="handleInvite"
          />
          <button
            type="button"
            class="h-10 px-3 rounded-[10px] bg-[var(--Button-primary-black)] text-[var(--text-onblack)] text-sm font-medium hover:opacity-90 disabled:opacity-50"
            :disabled="!email.trim()"
            @click="handleInvite">
            {{ t('Invite') }}
          </button>
        </div>

        <div class="flex flex-col gap-1">
          <div class="text-[12px] font-medium text-[var(--text-tertiary)] mb-1">{{ t('People with access') }}</div>
          <div class="flex items-center gap-3 rounded-[10px] px-2 py-2">
            <div class="size-8 rounded-full bg-[var(--fill-blue)] text-white flex items-center justify-center text-sm font-medium">
              {{ ownerLetter }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm text-[var(--text-primary)] truncate">{{ ownerName }}</div>
              <div class="text-[12px] text-[var(--text-tertiary)]">{{ t('Owner') }}</div>
            </div>
          </div>
          <div
            v-for="person in collaborators"
            :key="person.email"
            class="flex items-center gap-3 rounded-[10px] px-2 py-2 hover:bg-[var(--fill-tsp-white-main)]">
            <div class="size-8 rounded-full bg-[var(--fill-tsp-white-dark)] text-[var(--text-secondary)] flex items-center justify-center text-sm font-medium">
              {{ person.email.charAt(0).toUpperCase() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm text-[var(--text-primary)] truncate">{{ person.email }}</div>
              <div class="text-[12px] text-[var(--text-tertiary)]">{{ t('Can edit') }}</div>
            </div>
            <button
              type="button"
              class="text-[12px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
              @click="removeCollaborator(person.email)">
              {{ t('Remove') }}
            </button>
          </div>
          <div v-if="collaborators.length === 0" class="text-[13px] text-[var(--text-tertiary)] px-2 py-3">
            {{ t('No collaborators yet') }}
          </div>
        </div>

        <div class="border-t border-[var(--border-main)] pt-3 text-[12px] text-[var(--text-tertiary)]">
          {{ t('Collaboration invites are stored locally until the backend is available.') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { X } from 'lucide-vue-next';
import { useAuth } from '../composables/useAuth';
import { showErrorToast, showSuccessToast } from '../utils/toast';

const props = defineProps<{
  visible: boolean;
  sessionId?: string;
}>();

const emit = defineEmits<{ (e: 'close'): void }>();

const { t } = useI18n();
const { currentUser } = useAuth();
const email = ref('');
const collaborators = ref<{ email: string }[]>([]);

const ownerName = computed(() => currentUser.value?.fullname || t('Anonymous User'));
const ownerLetter = computed(() => ownerName.value.charAt(0).toUpperCase() || 'M');

const storageKey = computed(() => `manus-collab:${props.sessionId || 'unknown'}`);

const load = () => {
  if (!props.sessionId) {
    collaborators.value = [];
    return;
  }
  try {
    const raw = localStorage.getItem(storageKey.value);
    collaborators.value = raw ? JSON.parse(raw) : [];
  } catch {
    collaborators.value = [];
  }
};

const persist = () => {
  if (!props.sessionId) return;
  localStorage.setItem(storageKey.value, JSON.stringify(collaborators.value));
};

watch(() => props.visible, (v) => {
  if (v) {
    email.value = '';
    load();
  }
});

const handleInvite = () => {
  const value = email.value.trim().toLowerCase();
  if (!value) return;
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    showErrorToast(t('Please enter a valid email address'));
    return;
  }
  if (collaborators.value.some((c) => c.email === value)) {
    showErrorToast(t('Already invited'));
    return;
  }
  collaborators.value = [...collaborators.value, { email: value }];
  persist();
  email.value = '';
  showSuccessToast(t('Invitation added'));
};

const removeCollaborator = (addr: string) => {
  collaborators.value = collaborators.value.filter((c) => c.email !== addr);
  persist();
};
</script>
