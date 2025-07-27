import { ref } from 'vue';

const visible = ref(false);

export function useSessionFileList() {
    const showSessionFileList = () => {
        visible.value = true;
    }

    const hideSessionFileList = () => {
        visible.value = false;
    }

    return {
        visible,
        showSessionFileList,
        hideSessionFileList
    }
} 