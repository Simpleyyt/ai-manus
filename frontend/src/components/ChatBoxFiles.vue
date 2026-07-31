<template>
    <div v-if="files.length > 0" class="w-full relative rounded-md overflow-hidden flex-shrink-0 pb-3 -mb-3">
        <div v-if="canScrollLeft"
            class="absolute top-0 bottom-0 left-0 z-10 flex h-[54px] items-center gap-2.5 px-3 cursor-pointer"
            style="background-image: linear-gradient(270deg, var(--gradual-white-0) 0%, var(--background-menu-white) 100%);">
            <div
                class="flex h-7 w-7 items-center justify-center rounded-full border border-[var(--border-main)] bg-[var(--background-menu-white)] overflow-hidden cursor-pointer hover:bg-[var(--fill-tsp-primary)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)] backdrop-blur-[40px]">
                <div @click="scrollLeft"
                    class="flex w-full h-full items-center justify-center bg-[var(--background-menu-white)] cursor-pointer hover:bg-[var(--fill-tsp-white-main)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)]">
                    <ChevronLeft :size="14" />
                </div>
            </div>
        </div>
        <div ref="scrollContainer" @scroll="onScroll"
            class="w-full h-full overflow-y-hidden overflow-x-auto scrollbar-hide pb-[10px] -mb-[10px] ps-[10px] pe-2 flex">
            <div class="flex gap-3">
                <template v-for="file in files" :key="file.file_id">
                    <!-- Official image thumb: 54×54 rounded-[12px] preview -->
                    <div v-if="isImageAttachment(file)"
                        @click="handleFileClick(file)"
                        class="rounded-[12px] h-[54px] w-[54px] border border-[var(--border-main)] group/attach relative flex justify-center items-center flex-shrink-0 overflow-hidden cursor-pointer"
                        data-testid="chatbox-attach-image">
                        <img v-if="previewSrc(file)"
                            :src="previewSrc(file)!"
                            :alt="file.filename"
                            class="max-h-full max-w-full object-cover w-full h-full" />
                        <div v-else
                            class="flex items-center justify-center w-full h-full bg-[var(--fill-tsp-white-main)]">
                            <component :is="getFileType(file.filename).icon" />
                        </div>
                        <div v-if="file.status === 'uploading'"
                            class="absolute inset-0 flex justify-center items-center bg-[var(--fill-black)]">
                            <div class="border rounded-full animate-spin border-[3px] border-t-[var(--text-white)] border-r-transparent border-b-transparent border-l-transparent w-6 h-6" />
                        </div>
                        <div v-else-if="file.status === 'failed'"
                            class="absolute inset-0 flex justify-center items-center bg-[var(--fill-black)]/70">
                            <RefreshCcw @click.stop="retryUpload(file)"
                                class="clickable hover:opacity-85 cursor-pointer text-white"
                                :size="16" />
                        </div>
                        <button type="button" @click.stop="removeFile(file.file_id)"
                            class="hidden touch-device:flex group-hover/attach:flex rounded-full p-[2px] bg-[var(--icon-tertiary)] transition-all duration-200 hover:opacity-85 absolute end-1 top-1">
                            <X class="text-white" :size="10" />
                        </button>
                    </div>
                    <!-- Non-image: wide file chip -->
                    <div v-else @click="handleFileClick(file)"
                        class="flex items-center gap-1.5 p-2 pr-2.5 w-[280px] rounded-[10px] bg-[var(--fill-tsp-white-main)] group/attach relative overflow-hidden cursor-pointer hover:bg-[var(--fill-tsp-white-dark)]"
                        data-testid="chatbox-attach-file">
                        <div class="flex items-center justify-center w-8 h-8 rounded-md">
                            <div class="relative flex items-center justify-center">
                                <LoadingSpinnerIcon v-if="file.status === 'uploading'">
                                    <component :is="getFileType(file.filename).icon" />
                                </LoadingSpinnerIcon>
                                <component v-else :is="getFileType(file.filename).icon" />
                            </div>
                        </div>
                        <div class="flex flex-col gap-0.5 flex-1 min-w-0">
                            <div class="flex-1 min-w-0 flex items-center">
                                <div
                                    class="text-sm text-[var(--text-primary)] text-ellipsis overflow-hidden whitespace-nowrap flex-1 min-w-0">
                                    {{ file.filename }}</div>
                                <button type="button" @click.stop="removeFile(file.file_id)"
                                    class="hidden touch-device:flex group-hover/attach:flex rounded-full p-[2px] bg-[var(--icon-tertiary)] transition-all duration-200 hover:opacity-85">
                                    <X class="text-white" :size="10" />
                                </button>
                            </div>
                            <div class="text-xs text-[var(--text-tertiary)]">
                                <div v-if="file.status === 'failed'"
                                    class="text-[var(--function-error)] text-xs flex items-center gap-1">
                                    {{ t('Upload failed') }}
                                    <RefreshCcw @click.stop="retryUpload(file)" class="clickable hover:opacity-85 cursor-pointer"
                                        :size="14" />
                                </div>
                                <div v-else-if="file.status === 'uploading'">{{ t('Uploading...') }}</div>
                                <div v-else>{{ getFileTypeText(file.filename) }} · {{ formatFileSize(file.size) }}</div>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </div>
        <div v-if="canScrollRight"
            class="absolute top-0 bottom-0 right-0 z-10 flex h-[54px] items-center gap-2.5 px-3 cursor-pointer"
            style="background-image: linear-gradient(90deg, var(--gradual-white-0) 0%, var(--background-menu-white) 100%);">
            <div
                class="flex h-7 w-7 items-center justify-center rounded-full border border-[var(--border-main)] bg-[var(--background-menu-white)] overflow-hidden cursor-pointer hover:bg-[var(--fill-tsp-primary)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)] backdrop-blur-[40px]">
                <div @click="scrollRight"
                    class="flex w-full h-full items-center justify-center bg-[var(--background-menu-white)] cursor-pointer hover:bg-[var(--fill-tsp-white-main)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)]">
                    <ChevronRight :size="14" />
                </div>
            </div>
        </div>
    </div>
    <!-- Hidden file input -->
    <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />
</template>

<script setup lang="ts">
import { ChevronLeft, ChevronRight } from 'lucide-vue-next';
import type { FileInfo } from '../api/file';
import { uploadFile as apiUploadFile, getFileDownloadUrl } from '../api/file';
import { getFileType, getFileTypeText, formatFileSize, isImageFile } from '../utils/fileType';
import { useI18n } from 'vue-i18n';
import { ref, nextTick, watch, onMounted, onUnmounted, computed } from 'vue';
import { X, RefreshCcw } from 'lucide-vue-next';
import LoadingSpinnerIcon from './icons/LoadingSpinnerIcon.vue';
import { useFilePreviewer } from '../composables/useFilePreviewer';

const { t } = useI18n();

// Extended FileInfo type to include upload status + local preview
export interface ExtendedFileInfo extends FileInfo {
    status?: 'uploading' | 'success' | 'failed';
    file?: File | null;
    /** Local blob: or remote URL for image thumbnail */
    previewUrl?: string;
}

const props = defineProps<{
    attachments: ExtendedFileInfo[];
}>();

const emit = defineEmits<{
    (e: 'update:attachments', value: ExtendedFileInfo[]): void;
}>();

const { showFilePreviewer } = useFilePreviewer();

const files = computed(() => props.attachments);
const fileInput = ref<HTMLInputElement>();
const scrollContainer = ref<HTMLElement>();

const canScrollLeft = ref(false);
const canScrollRight = ref(false);

const isImageAttachment = (file: ExtendedFileInfo) =>
    isImageFile(file.filename, file.content_type);

const previewSrc = (file: ExtendedFileInfo) => file.previewUrl || undefined;

const revokePreview = (file: ExtendedFileInfo) => {
    if (file.previewUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(file.previewUrl);
    }
};

const uploadFile = () => {
    fileInput.value?.click();
};

const setFiles = (value: ExtendedFileInfo[]) => {
    emit('update:attachments', value);
};

const replaceFile = (fileId: string, replacement: ExtendedFileInfo) => {
    setFiles(files.value.map(f => f.file_id === fileId ? replacement : f));
};

const handleFileSelect = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    const selectedFiles = target.files;

    if (!selectedFiles || selectedFiles.length === 0) {
        return;
    }

    for (const file of Array.from(selectedFiles)) {
        await processFileUpload(file);
    }

    target.value = '';
};

const processFileUpload = async (file: File) => {
    const previewUrl = isImageFile(file.name, file.type)
        ? URL.createObjectURL(file)
        : undefined;

    const tempFileInfo: ExtendedFileInfo = {
        file_id: `temp-${Date.now()}-${Math.random()}`,
        filename: file.name,
        content_type: file.type,
        size: file.size,
        upload_date: new Date().toISOString(),
        status: 'uploading',
        file: file,
        previewUrl,
    };

    setFiles([...files.value, tempFileInfo]);

    try {
        const uploadedFile = await apiUploadFile(file);

        // Keep blob preview for images after upload (official uses blob until send)
        replaceFile(tempFileInfo.file_id, {
            ...uploadedFile,
            status: 'success',
            file: null,
            previewUrl,
        });
    } catch (error) {
        console.error('Upload failed:', error);
        replaceFile(tempFileInfo.file_id, { ...tempFileInfo, status: 'failed' });
    }
};

const removeFile = (fileId: string) => {
    const target = files.value.find(f => f.file_id === fileId);
    if (target) revokePreview(target);
    setFiles(files.value.filter(f => f.file_id !== fileId));
};

const retryUpload = async (fileInfo: ExtendedFileInfo) => {
    if (!fileInfo.file) {
        return;
    }

    replaceFile(fileInfo.file_id, { ...fileInfo, status: 'uploading' });

    try {
        const uploadedFile = await apiUploadFile(fileInfo.file);

        replaceFile(fileInfo.file_id, {
            ...uploadedFile,
            status: 'success',
            file: null,
            previewUrl: fileInfo.previewUrl,
        });
    } catch (error) {
        console.error('Retry upload failed:', error);
        replaceFile(fileInfo.file_id, { ...fileInfo, status: 'failed' });
    }
};

const ensureRemoteImagePreview = async (file: ExtendedFileInfo) => {
    if (!isImageAttachment(file) || file.previewUrl || file.status === 'uploading') return;
    if (!file.file_id || file.file_id.startsWith('temp-')) return;
    try {
        const url = await getFileDownloadUrl(file);
        replaceFile(file.file_id, { ...file, previewUrl: url });
    } catch (e) {
        console.error('Failed to resolve image preview URL', e);
    }
};

const updateScrollButtons = () => {
    if (!scrollContainer.value) return;

    const container = scrollContainer.value;
    const scrollLeft = container.scrollLeft;
    const scrollWidth = container.scrollWidth;
    const clientWidth = container.clientWidth;

    canScrollLeft.value = scrollLeft > 0;
    canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 5;
};

const onScroll = () => {
    updateScrollButtons();
};

const scrollLeft = () => {
    if (scrollContainer.value) {
        scrollContainer.value.scrollBy({
            left: -120,
            behavior: 'smooth'
        });
    }
};

const scrollRight = () => {
    if (scrollContainer.value) {
        scrollContainer.value.scrollBy({
            left: 120,
            behavior: 'smooth'
        });
    }
};

watch(files, async (list) => {
    await nextTick();
    updateScrollButtons();
    for (const f of list) {
        void ensureRemoteImagePreview(f);
    }
}, { deep: true, immediate: true });

onMounted(() => {
    nextTick(() => {
        updateScrollButtons();
    });
});

onUnmounted(() => {
    for (const f of files.value) {
        revokePreview(f);
    }
});

const isAllUploaded = computed(() => {
    return files.value.every(file => !file.status || file.status === 'success');
});

const handleFileClick = (file: ExtendedFileInfo) => {
    if (file.status === 'success') {
        showFilePreviewer(file);
    }
};

defineExpose({
    uploadFile,
    isAllUploaded
});
</script>
