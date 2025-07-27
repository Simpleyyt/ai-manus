<template>
  <div className="h-screen flex overflow-hidden bg-white">
    <LeftPanel />
    <div className="flex-1 min-w-0 h-full py-0 pr-0 relative">
      <div className="flex h-full bg-[var(--background-gray-main)]">
        <div class="flex flex-1 min-w-0 min-h-0">
          <router-view />
          <FilePanel />
        </div>
      </div>
    </div>
  </div>
  <TakeOverView />
  <ContextMenu />
  <CustomDialog />
  <SessionFileList />
</template>

<script setup lang="ts">
import LeftPanel from '@/components/LeftPanel.vue';
import CustomDialog from '@/components/CustomDialog.vue';
import ContextMenu from '@/components/ContextMenu.vue';
import TakeOverView from '@/components/TakeOverView.vue';
import SessionFileList from '@/components/SessionFileList.vue';
import FilePanel from '@/components/FilePanel.vue';
</script>
