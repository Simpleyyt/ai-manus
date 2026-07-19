<template>
    <div v-if="dialogVisible" class="absolute z-[1000] pointer-events-auto">
        <div class="w-full h-full bg-black/60 backdrop-blur-[4px] fixed inset-0 data-[state=open]:animate-dialog-bg-fade-in data-[state=closed]:animate-dialog-bg-fade-out"
            style="position: fixed; overflow: auto; inset: 0px;" @click="handleBackdropClick"></div>
        <div role="dialog"
            class="bg-[var(--background-menu-white)] rounded-[20px] border border-white/5 fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-w-[95%] max-h-[95%] overflow-auto data-[state=open]:animate-dialog-slide-in-from-bottom data-[state=closed]:animate-dialog-slide-out-to-bottom w-[440px]">
            <div class="pt-5 pb-[10px] px-5">
                <h3 class="text-[var(--text-primary)] text-[18px] leading-[24px] font-semibold flex items-center">
                    {{ dialogConfig.title }}</h3>
                <div
                    class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md absolute top-[20px] ltr:right-[12px] rtl:left-[12px]"
                    @click="handleCancel"
                    :aria-label="$t('Close Dialog')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-x h-5 w-5 text-[var(--icon-tertiary)]">
                        <path d="M18 6 6 18"></path>
                        <path d="m6 6 12 12"></path>
                    </svg>
                </div>
            </div>
            <div v-if="dialogConfig.content" class="px-5 py-3 text-[var(--text-tertiary)] text-sm">
                {{ dialogConfig.content }}
            </div>
            <div v-if="dialogConfig.inputEnabled" class="px-5 pb-1">
                <input
                    v-model="dialogConfig.inputValue"
                    type="text"
                    class="w-full h-10 px-3 rounded-[10px] border border-[var(--border-main)] bg-[var(--fill-tsp-white-main)] text-[var(--text-primary)] text-sm outline-none focus:border-[var(--border-dark)]"
                    :placeholder="dialogConfig.inputPlaceholder"
                    @keydown.enter.prevent="handleConfirm"
                    autofocus
                />
            </div>
            <div class="flex justify-end gap-2 p-5">
                <button
                    class="rounded-[10px] px-3 py-2 text-sm border border-[var(--border-btn-main)] bg-[var(--button-secondary)] text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-dark)] cursor-pointer transition-colors"
                    @click="handleCancel">{{ dialogConfig.cancelText }}</button>
                <button
                    :class="[
                        'rounded-[10px] px-3 py-2 text-sm flex flex-row gap-1 items-center cursor-pointer transition-colors',
                        dialogConfig.confirmType === 'danger' 
                            ? 'border border-[var(--Button-secondary-error-border)] bg-[var(--Button-secondary-error-fill)] text-[var(--function-error)] enabled:hover:bg-[var(--function-error)] enabled:hover:text-[var(--text-white)]'
                            : 'border border-[var(--border-btn-primary)] bg-[var(--button-primary)] text-[var(--text-white)] hover:bg-[var(--button-primary-hover)]'
                    ]"
                    @click="handleConfirm">{{ dialogConfig.confirmText }}</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useDialog } from '@/composables/useDialog'

// Use dialog composable directly
const { dialogVisible, dialogConfig, handleConfirm, handleCancel } = useDialog()

// Handle backdrop click
const handleBackdropClick = () => {
    handleCancel()
}
</script>