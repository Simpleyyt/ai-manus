<template>
    <div class="pointer-events-auto cursor-default">
        <div class="min-w-max inline-block transition-[transform,opacity,scale] duration-150" tabindex="-1"
            role="dialog">
            <div
                class="flex w-[300px] flex-col bg-[var(--background-menu-white)] rounded-[20px] border-[0.5px] border-[var(--border-dark)] shadow-[0px_8px_32px_0px_var(--shadow-XS)]">
                <div class="flex gap-2 px-4 pt-5 pb-3 w-full">
                    <div class="relative flex items-center justify-center font-bold cursor-pointer flex-shrink-0">
                        <div class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                            style="width: 48px; height: 48px; font-size: 24px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
                            {{ avatarLetter }}</div>
                    </div>
                    <div class="flex overflow-hidden flex-col justify-center">
                        <div class="flex gap-1 items-center w-full"><span
                                class="text-[var(--text-primary)] text-base font-semibold leading-[22px] truncate">{{
                                    currentUser?.fullname || t('Unknown User') }}</span></div><span
                            class="text-[var(--text-tertiary)] text-[13px] font-normal leading-[18px] truncate">{{
                                currentUser?.email || t('No email') }}</span>
                    </div>
                </div>
                <div class="flex flex-col gap-3 px-3 pb-3">
                    <div class="flex flex-col gap-1">
                        <div class="w-full h-[1px] my-1 bg-[var(--border-main)]"></div>
                        <div
                            class="flex gap-3 items-center p-2 rounded-lg cursor-pointer text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                            @click="handleAccountClick">
                            <div class="flex-shrink-0 w-5 h-5">
                                <User :size="20" />
                            </div>
                            <span
                                class="overflow-hidden flex-1 text-sm font-medium leading-5 whitespace-nowrap text-ellipsis">{{
                                t('Account') }}</span>
                        </div>
                        <div
                            class="flex gap-3 items-center p-2 rounded-lg cursor-pointer text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                            @click="handleSettingsClick">
                            <div class="flex-shrink-0 w-5 h-5">
                                <Settings2 :size="20" />
                            </div>
                            <span
                                class="overflow-hidden flex-1 text-sm font-medium leading-5 whitespace-nowrap text-ellipsis">{{
                                t('Settings') }}</span>
                        </div>
                        <div class="w-full h-[1px] my-1 bg-[var(--border-main)]"></div>
                        <div v-if="authProvider !== 'none'"
                            class="flex gap-3 items-center p-2 rounded-lg cursor-pointer hover:bg-[var(--fill-tsp-white-main)] text-[var(--function-error)]"
                            @click="handleLogout">
                            <div class="flex-shrink-0 w-5 h-5">
                                <LogOut :size="20" />
                            </div>
                            <span
                                class="overflow-hidden flex-1 text-sm font-medium leading-5 whitespace-nowrap text-ellipsis">{{
                                t('Logout') }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuth } from '../composables/useAuth';
import { useSettingsDialog } from '../composables/useSettingsDialog';
import { getAuthProvider } from '../api/config';
import { LogOut, User, Settings2 } from 'lucide-vue-next';

const router = useRouter();
const { t } = useI18n();
const { currentUser, logout } = useAuth();
const { openSettingsDialog } = useSettingsDialog();
const authProvider = computed(() => getAuthProvider());

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
    return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

// Handle Account click - open settings dialog with account tab
const handleAccountClick = () => {
    openSettingsDialog('account');
};

// Handle Settings click - open settings dialog with settings tab
const handleSettingsClick = () => {
    openSettingsDialog('settings');
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