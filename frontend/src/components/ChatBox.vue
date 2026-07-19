<template>
    <div class="pb-3 relative bg-[var(--background-gray-main)]">
        <!-- 结构复刻自 manus.im 首页输入框 -->
        <div
            class="flex flex-col gap-3 rounded-[22px] transition-all relative bg-[var(--background-menu-white)] py-3 max-h-[300px] shadow-[0px_12px_32px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-main)] focus-within:border-black/20 dark:focus-within:border-[var(--border-dark)]">
            <ChatBoxFiles ref="chatBoxFileListRef" :attachments="attachments"
                @update:attachments="emit('update:attachments', $event)" />
            <div class="overflow-auto ps-4 pe-2 min-h-[46px] w-full text-[15px] leading-[24px]">
                <textarea
                    class="flex rounded-md border-input focus-visible:outline-none focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 overflow-hidden flex-1 bg-transparent p-0 pt-[1px] border-0 focus-visible:ring-0 focus-visible:ring-offset-0 w-full placeholder:text-[var(--text-disable)] text-[15px] leading-[24px] shadow-none resize-none min-h-[40px]"
                    :rows="rows" :value="modelValue"
                    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
                    @compositionstart="isComposing = true" @compositionend="isComposing = false"
                    @keydown.enter.exact="handleEnterKeydown" :placeholder="placeholderText"
                    :style="{ height: '46px' }"></textarea>
            </div>
            <div class="px-3"></div>
            <footer class="flex gap-2 px-3 items-center">
                <!-- Manus-style + menu (local files) -->
                <div class="relative" ref="plusMenuRef">
                    <button type="button" @click="showPlusMenu = !showPlusMenu"
                        class="rounded-full border border-[var(--border-main)] inline-flex items-center justify-center gap-1 clickable cursor-pointer text-xs text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-light)] w-8 h-8 p-0 shrink-0"
                        :title="t('Add files and more')"
                        aria-expanded="false" aria-haspopup="dialog">
                        <Plus :size="16" />
                    </button>
                    <div v-if="showPlusMenu"
                        class="absolute bottom-[calc(100%+8px)] left-0 z-50 min-w-[200px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] py-1">
                        <button type="button"
                            class="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                            @click="handleAddLocalFiles">
                            <Paperclip :size="16" class="text-[var(--icon-tertiary)]" />
                            {{ t('Add local files') }}
                        </button>
                    </div>
                </div>
                <button @click="uploadFile"
                    class="rounded-full border border-[var(--border-main)] inline-flex items-center justify-center gap-1 clickable cursor-pointer text-xs text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-light)] w-8 h-8 p-0 shrink-0"
                    :title="t('Add local files')"
                    aria-expanded="false" aria-haspopup="dialog">
                    <Paperclip :size="16" />
                </button>
                <div class="flex gap-2 ml-auto">
                    <button v-if="!isRunning || sendEnabled || hideStopButton"
                        class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors text-sm rounded-full p-0 w-8 h-8 min-w-0 hover:opacity-90"
                        :class="!sendEnabled ? 'cursor-not-allowed bg-[var(--fill-tsp-white-dark)] hover:opacity-100' : 'cursor-pointer bg-[var(--Button-primary-black)]'"
                        @click="handleSubmit">
                        <SendIcon :disabled="!sendEnabled" />
                    </button>
                    <button v-else-if="!hideStopButton" @click="handleStop"
                        class="inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-colors bg-[var(--Button-primary-black)] text-[var(--text-onblack)] gap-[4px] hover:opacity-90 rounded-full p-0 w-8 h-8">
                        <div class="w-[10px] h-[10px] bg-[var(--icon-onblack)] rounded-[2px]">
                        </div>
                    </button>
                </div>
            </footer>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import SendIcon from './icons/SendIcon.vue';
import { useI18n } from 'vue-i18n';
import ChatBoxFiles from './ChatBoxFiles.vue';
import { Paperclip, Plus } from 'lucide-vue-next';
import type { FileInfo } from '../api/file';

const { t } = useI18n();
const hasTextInput = ref(false);
const isComposing = ref(false);
const chatBoxFileListRef = ref();
const showPlusMenu = ref(false);
const plusMenuRef = ref<HTMLElement | null>(null);

const props = withDefaults(defineProps<{
    modelValue: string;
    rows: number;
    isRunning: boolean;
    attachments: FileInfo[];
    hideStopButton?: boolean;
    allowSendFilesOnly?: boolean;
    /** Manus session detail uses "Send message to Manus"; home keeps the task prompt. */
    placeholder?: string;
}>(), {
    placeholder: undefined,
});

const placeholderText = computed(() => props.placeholder || t('Give Manus a task to work on...'));

const sendEnabled = computed(() => {
    const hasFiles = (props.attachments?.length ?? 0) > 0;
    const allUploaded = chatBoxFileListRef.value?.isAllUploaded ?? true;
    if (props.allowSendFilesOnly) {
        return hasTextInput.value || (hasFiles && allUploaded);
    }
    return hasTextInput.value && (!hasFiles || allUploaded);
});

const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void;
    (e: 'update:attachments', value: FileInfo[]): void;
    (e: 'submit'): void;
    (e: 'stop'): void;
}>();

const handleEnterKeydown = (event: KeyboardEvent) => {
    if (isComposing.value) {
        // If in input method composition state, do nothing and allow default behavior
        return;
    }

    // Not in input method composition state and has text input, prevent default behavior and submit
    if (sendEnabled.value) {
        event.preventDefault();
        handleSubmit();
    }
};

const handleSubmit = () => {
    if (!sendEnabled.value) return;
    emit('submit');
};

const handleStop = () => {
    emit('stop');
};

const uploadFile = () => {
    chatBoxFileListRef.value?.uploadFile();
};

const handleAddLocalFiles = () => {
    showPlusMenu.value = false;
    uploadFile();
};

const handleClickOutside = (event: MouseEvent) => {
    if (showPlusMenu.value && plusMenuRef.value && !plusMenuRef.value.contains(event.target as Node)) {
        showPlusMenu.value = false;
    }
};

onMounted(() => {
    document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('mousedown', handleClickOutside);
});

watch(() => props.modelValue, (value) => {
    hasTextInput.value = value.trim() !== '';
});
</script>