import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'
import { frappeRequest } from '@/utils/api'

export const visible = ref(false)

export const notifications = createResource({
  url: 'invite.api.notification.get_notifications',
  initialData: [],
  auto: true,
})

export const unreadNotificationsCount = computed(
  () => notifications.data?.filter((n) => !n.read).length || 0,
)

let markReadResource = null

function ensureMarkReadResource() {
  if (!markReadResource) {
    markReadResource = createResource({
      url: 'invite.api.notification.mark_as_read',
      onSuccess: () => {
        notifications.reload()
      },
    })
  }
  return markReadResource
}

export function mark_as_read(doc) {
  const resource = ensureMarkReadResource()
  resource.params = { doc: doc }
  resource.reload()
}

export function mark_doc_as_read(doc) {
  mark_as_read(doc)
  visible.value = false
}

export function toggle() {
  visible.value = !visible.value
}
