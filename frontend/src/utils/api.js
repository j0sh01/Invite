import { frappeRequest as originalFrappeRequest } from 'frappe-ui'
import { useNotifications } from '@/composables/notifications'

const { showError } = useNotifications()

export function frappeRequest(options) {
  return originalFrappeRequest({
    ...options,
    onError(e) {
      if (e.messages?.length) {
        showError(e.messages)
      }
      if (options.onError) {
        options.onError(e)
      }
    },
  })
}
