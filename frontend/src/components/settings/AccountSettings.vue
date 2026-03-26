<template>
    <div class="pt-4 flex justify-between items-center self-stretch gap-[12px]">
        <div class="flex items-center gap-4 flex-auto overflow-y-visible min-w-0">
            <div
                class="relative flex items-center justify-center font-bold cursor-pointer flex-shrink-0 flex-shrink-0 flex-grow-0">
                <div class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                    style="width: 64px; height: 64px; font-size: 32px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
                    {{ avatarLetter }}</div>
            </div>
            <div class="flex flex-col content-center items-start flex-auto overflow-hidden">
                <div class="flex items-center gap-1 w-full"><span
                        class="text-[var(--text-primary)] text-[20px] font-semibold leading-[26px] truncate">{{ currentUser?.fullname || t('Unknown User') }}</span></div>
                <div
                    class="text-[14px] font-normal leading-[22px] text-[var(--text-tertiary)] whitespace-nowrap overflow-hidden text-ellipsis">
                    {{ currentUser?.email || t('No email') }}</div>
            </div>
        </div>
        <div class="self-start md:self-center flex gap-2">
            <div
                class="flex items-center justify-center cursor-pointer bg-[var(--Button-primary-white)] shadow-[0px_0.5px_3px_0px_var(--shadow-S)] hover:opacity-80 active:opacity-70 transition-opacity size-9 rounded-[10px]"
                @click="handleProfileClick">
                <UserCog class="size-4 md:size-5 text-[var(--icon-secondary)]" />
            </div>
            <div v-if="authProvider !== 'none'"
                class="flex items-center justify-center cursor-pointer bg-[var(--Button-primary-white)] shadow-[0px_0.5px_3px_0px_var(--shadow-S)] hover:opacity-80 active:opacity-70 transition-opacity size-9 rounded-[10px]"
                @click="handleLogout">
                <LogOut class="size-4 md:size-5 text-[var(--function-error)]" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { UserCog, LogOut } from 'lucide-vue-next';
import { useAuth } from '../../composables/useAuth';
import { getAuthProvider } from '../../api/config';

const router = useRouter();
const { t } = useI18n();
const { currentUser, logout } = useAuth();
const authProvider = computed(() => getAuthProvider());

// Emit events for parent components
const emit = defineEmits<{
  navigateToProfile: []
}>();

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

// Handle profile icon click
const handleProfileClick = () => {
  emit('navigateToProfile');
};

// Handle logout action
const handleLogout = async () => {
  try {
    await logout();
    router.push('/login');
  } catch (error) {
    console.error('Logout failed:', error);
  }
};


</script>
