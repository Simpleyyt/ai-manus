import { ref, computed, onMounted, onUnmounted } from 'vue';
import { formatRelativeTime, formatCustomTime } from '../utils/time';
import { useI18n } from 'vue-i18n';

export function useRelativeTime() {
  // Create a reactive current time variable to trigger re-rendering
  const currentTime = ref(Date.now());

  // Set a timer to update the time every minute
  let timer: number | null = null;

  onMounted(() => {
    timer = window.setInterval(() => {
      currentTime.value = Date.now();
    }, 60000); // Update every minute
  });

  onUnmounted(() => {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  });

  // Calculate relative time, depends on currentTime for automatic updates
  const relativeTime = computed(() => {
    // Depends on currentTime, recalculate when currentTime updates
    void currentTime.value;
    return (timestamp: number) => formatRelativeTime(timestamp);
  });

  return {
    relativeTime
  };
}

export function useCustomTime() {
  const { t, locale } = useI18n();
  
  // Create a reactive current time variable to trigger re-rendering
  const currentTime = ref(Date.now());

  // Set a timer to update the time every minute
  let timer: number | null = null;

  onMounted(() => {
    timer = window.setInterval(() => {
      currentTime.value = Date.now();
    }, 60000); // Update every minute
  });

  onUnmounted(() => {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  });

  // Calculate custom formatted time, depends on currentTime for automatic updates
  const customTime = computed(() => {
    // Depends on currentTime, recalculate when currentTime updates
    void currentTime.value;
    return (timestamp: number) => formatCustomTime(timestamp, t, locale.value);
  });

  return {
    customTime
  };
} 