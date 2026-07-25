<template>
  <div class="h-screen flex overflow-hidden bg-white">
    <SessionSidebar />
    <div class="flex-1 min-w-0 h-full py-0 pr-0 relative">
      <div class="flex h-full bg-[var(--background-gray-main)]">
        <div class="flex flex-1 min-w-0 min-h-0">
          <router-view />
          <FilePreviewer v-if="!hideFilePreviewer" />
        </div>
      </div>
    </div>
  </div>
  <TakeOverView />
  <CustomDialog />
  <SessionFileList />
  <SettingsDialog />
  <ContextMenu />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import SessionSidebar from '@/components/SessionSidebar.vue';
import CustomDialog from '@/components/ui/CustomDialog.vue';
import ContextMenu from '@/components/ui/ContextMenu.vue';
import TakeOverView from '@/components/TakeOverView.vue';
import SessionFileList from '@/components/SessionFileList.vue';
import FilePreviewer from '@/components/FilePreviewer.vue';
import SettingsDialog from '@/components/settings/SettingsDialog.vue';

const route = useRoute();
// Project page is a full two-column layout; keep FilePreviewer off there.
// Library reuses FilePreviewer for attachment preview (official openFilePreview).
const hideFilePreviewer = computed(() => route.path.startsWith('/project/'));

</script>
