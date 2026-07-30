import { ref, watch } from 'vue'

const NOTIFICATION_KEY = 'manus-browser-notifications'
const SOUND_KEY = 'manus-sound-reminder'

function readBool(key: string, fallback: boolean): boolean {
  try {
    const raw = localStorage.getItem(key)
    if (raw === null) return fallback
    return JSON.parse(raw) === true
  } catch {
    return fallback
  }
}

function writeBool(key: string, value: boolean): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* ignore */
  }
}

const browserNotificationsEnabled = ref(readBool(NOTIFICATION_KEY, false))
const soundReminderEnabled = ref(readBool(SOUND_KEY, false))

watch(browserNotificationsEnabled, (v) => writeBool(NOTIFICATION_KEY, v))
watch(soundReminderEnabled, (v) => writeBool(SOUND_KEY, v))

export function useChromePrefs() {
  const setBrowserNotifications = async (enabled: boolean) => {
    if (enabled) {
      if (typeof Notification === 'undefined') {
        browserNotificationsEnabled.value = false
        return false
      }
      const permission = await Notification.requestPermission()
      const ok = permission === 'granted'
      browserNotificationsEnabled.value = ok
      return ok
    }
    browserNotificationsEnabled.value = false
    return true
  }

  const setSoundReminder = (enabled: boolean) => {
    soundReminderEnabled.value = enabled
  }

  return {
    browserNotificationsEnabled,
    soundReminderEnabled,
    setBrowserNotifications,
    setSoundReminder,
  }
}
