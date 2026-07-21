import { ref } from 'vue'

const toasts = ref([])
let toastId = 0

export function useNotifications() {
  function showToast(message, type = 'error', duration = 5000) {
    const id = ++toastId
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  function showError(messages) {
    const msgs = Array.isArray(messages) ? messages : [messages]
    msgs.forEach(msg => {
      if (msg) showToast(msg, 'error')
    })
  }

  function dismissToast(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, showToast, showError, dismissToast }
}
