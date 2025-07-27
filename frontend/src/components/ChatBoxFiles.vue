<template>
    <div v-if="files.length > 0" class="w-full relative rounded-md overflow-hidden flex-shrink-0 pb-3 -mb-3">
        <div v-if="canScrollLeft"
            class="absolute top-0 bottom-0 left-0 z-10 flex h-full items-center gap-2.5 px-3 cursor-pointer"
            style="background-image: linear-gradient(270deg, var(--gradual-white-0) 0%, var(--fill-input-chat) 100%);">
            <div
                class="flex h-7 w-7 items-center justify-center rounded-full border border-[var(--border-white)] bg-[var(--background-menu-white)] overflow-hidden cursor-pointer hover:bg-[var(--fill-tsp-primary)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)] backdrop-blur-[40px]">
                <div @click="scrollLeft"
                    class="flex w-full h-full items-center justify-center bg-[var(--background-menu-white)] cursor-pointer hover:bg-[var(--fill-tsp-white-main)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)]">
                    <ChevronLeft :size="14" />
                </div>
            </div>
        </div>
        <div ref="scrollContainer" @scroll="onScroll"
            class="w-full overflow-y-hidden overflow-x-auto scrollbar-hide pb-[10px] -mb-[10px] pl-[10px] pr-2 flex">
            <div class="flex gap-3">
                <div v-for="file in files" :key="file.file_id" @click="handleFileClick(file)"
                    class="flex items-center gap-1.5 p-2 pr-2.5 w-[280px] rounded-[10px] bg-[var(--fill-tsp-white-main)] group/attach relative overflow-hidden cursor-pointer hover:bg-[var(--fill-tsp-white-dark)]">
                    <div class="flex items-center justify-center w-8 h-8 rounded-md">
                        <div class="relative flex items-center justify-center">
                            <!-- Loading state -->
                            <LoadingSpinnerIcon v-if="file.status === 'uploading'">
                                <component :is="getFileType(file.filename).icon" />
                            </LoadingSpinnerIcon>
                            <!-- Normal state -->
                            <component v-else :is="getFileType(file.filename).icon" />
                        </div>
                    </div>
                    <div class="flex flex-col gap-0.5 flex-1 min-w-0">
                        <div class="flex-1 min-w-0 flex items-center">
                            <div
                                class="text-sm text-[var(--text-primary)] text-ellipsis overflow-hidden whitespace-nowrap flex-1 min-w-0">
                                {{ file.filename }}</div>
                            <button @click.stop="removeFile(file.file_id)"
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
            </div>
        </div>
        <div v-if="canScrollRight"
            class="absolute top-0 bottom-0 right-0 z-10 flex h-full items-center gap-2.5 px-3 cursor-pointer"
            style="background-image: linear-gradient(90deg, var(--gradual-white-0) 0%, var(--fill-input-chat) 100%);">
            <div
                class="flex h-7 w-7 items-center justify-center rounded-full border border-[var(--border-white)] bg-[var(--background-menu-white)] overflow-hidden cursor-pointer hover:bg-[var(--fill-tsp-primary)] shadow-[0_0_1.25px_0_var(--shadow-M),0_5px_16px_0_var(--shadow-M)] backdrop-blur-[40px]">
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
import { uploadFile as apiUploadFile } from '../api/file';
import { getFileType, getFileTypeText, formatFileSize } from '../utils/fileType';
import { useI18n } from 'vue-i18n';
import { ref, nextTick, watch, onMounted, computed } from 'vue';
import { X, RefreshCcw } from 'lucide-vue-next';
import LoadingSpinnerIcon from './icons/LoadingSpinnerIcon.vue';
const { t } = useI18n();
import { useFilePanel } from '../composables/useFilePanel';

const props = defineProps<{
    attachments: FileInfo[];
}>();

const { showFilePanel } = useFilePanel();

// Extended FileInfo type to include upload status
interface ExtendedFileInfo extends FileInfo {
    status?: 'uploading' | 'success' | 'failed';
    file?: File | null; // Keep reference to original file for retry
}

const files = ref<ExtendedFileInfo[]>(props.attachments);
const fileInput = ref<HTMLInputElement>();
const scrollContainer = ref<HTMLElement>();

// Scroll state
const canScrollLeft = ref(false);
const canScrollRight = ref(false);

const uploadFile = () => {
    fileInput.value?.click();
};

const getFiles = () => {
    return files.value;
};

const handleFileSelect = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    const selectedFiles = target.files;

    if (!selectedFiles || selectedFiles.length === 0) {
        return;
    }

    // Process each selected file
    for (const file of Array.from(selectedFiles)) {
        await processFileUpload(file);
    }

    // Clear the input value to allow selecting the same file again
    target.value = '';
};

const processFileUpload = async (file: File) => {
    // Create temporary file info for UI
    const tempFileInfo: ExtendedFileInfo = {
        file_id: `temp-${Date.now()}-${Math.random()}`,
        filename: file.name,
        content_type: file.type,
        size: file.size,
        upload_date: new Date().toISOString(),
        status: 'uploading',
        file: file
    };

    // Add to files list with uploading status
    files.value.push(tempFileInfo);

    try {
        // Upload the file
        const uploadedFile = await apiUploadFile(file);

        // Update the file info with successful upload
        const index = files.value.findIndex(f => f.file_id === tempFileInfo.file_id);
        if (index !== -1) {
            files.value[index] = {
                ...uploadedFile,
                status: 'success',
                file: null
            };
        }
    } catch (error) {
        console.error('Upload failed:', error);

        // Update status to failed
        const index = files.value.findIndex(f => f.file_id === tempFileInfo.file_id);
        if (index !== -1) {
            files.value[index].status = 'failed';
        }
    }
};

const removeFile = (fileId: string) => {
    const index = files.value.findIndex(f => f.file_id === fileId);
    if (index !== -1) {
        files.value.splice(index, 1);
    }
};

const retryUpload = async (fileInfo: ExtendedFileInfo) => {
    if (!fileInfo.file) {
        return;
    }

    // Reset status to uploading
    fileInfo.status = 'uploading';

    try {
        // Retry upload
        const uploadedFile = await apiUploadFile(fileInfo.file);

        // Update with new file info
        const index = files.value.findIndex(f => f.file_id === fileInfo.file_id);
        if (index !== -1) {
            files.value[index] = {
                ...uploadedFile,
                status: 'success',
                file: null
            };
        }
    } catch (error) {
        console.error('Retry upload failed:', error);
        fileInfo.status = 'failed';
    }
};

// Check scroll position and update button visibility
const updateScrollButtons = () => {
    if (!scrollContainer.value) return;

    const container = scrollContainer.value;
    const scrollLeft = container.scrollLeft;
    const scrollWidth = container.scrollWidth;
    const clientWidth = container.clientWidth;

    canScrollLeft.value = scrollLeft > 0;
    canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 5; // 5px tolerance
};

// Handle scroll event
const onScroll = () => {
    updateScrollButtons();
};

const scrollLeft = () => {
    if (scrollContainer.value) {
        scrollContainer.value.scrollBy({
            left: -280, // Approximate width of one file item
            behavior: 'smooth'
        });
    }
};

const scrollRight = () => {
    if (scrollContainer.value) {
        scrollContainer.value.scrollBy({
            left: 280, // Approximate width of one file item
            behavior: 'smooth'
        });
    }
};

// Watch for changes in files to update scroll buttons
watch(files, async () => {
    await nextTick();
    updateScrollButtons();
}, { deep: true });

// Initialize scroll buttons on mount
onMounted(() => {
    nextTick(() => {
        updateScrollButtons();
    });
});

const isAllUploaded = computed(() => {
    return files.value.every(file => file.status === 'success');
});

const handleFileClick = (file: ExtendedFileInfo) => {
    if (file.status === 'success') {
        showFilePanel(file);
    }
};

defineExpose({
    uploadFile,
    getFiles,
    isAllUploaded
});
</script>