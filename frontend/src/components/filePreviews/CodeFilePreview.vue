<template>
    <section style="display: flex; position: relative; text-align: initial; width: 100%; height: 100%;">
        <div class="w-full h-full" data-keybinding-context="9" data-mode-id="c"
            style="width: 100%; --vscode-editorCodeLens-lineHeight: 15px; --vscode-editorCodeLens-fontSize: 10px; --vscode-editorCodeLens-fontFeatureSettings: 'liga' off, 'calt' off;">

          <MonacoEditor
            :value="content"
            :filename="file.filename"
            :read-only="true"
            theme="vs"
            :line-numbers="'off'"
            :word-wrap="'on'"
            :minimap="false"
            :scroll-beyond-last-line="false"
            :automatic-layout="true"
          />
        </div>
    </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import MonacoEditor from '../MonacoEditor.vue';
import type { FileInfo } from '../../api/file';
import { downloadFile } from '../../api/file';

const content = ref('');

const props = defineProps<{
    file: FileInfo;
}>();

watch(() => props.file.file_id, async (fileId) => {
    if (!fileId) return;
    try {
        const blob = await downloadFile(fileId);
        const text = await blob.text();
        content.value = text;
    } catch (error) {
        console.error('Failed to load file content:', error);
        content.value = '(Failed to load file content)';
    }
}, { immediate: true });
</script>