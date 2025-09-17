import { ref } from 'vue';

const visible = ref(false);
const shared = ref(false);

export function useSessionFileList() {
    const showSessionFileList = (isShared: boolean = false) => {
        visible.value = true;
        shared.value = isShared;
    }

    const hideSessionFileList = () => {
        visible.value = false;
    }

    return {
        visible,
        shared,
        showSessionFileList,
        hideSessionFileList
    }
} 