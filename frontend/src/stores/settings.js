import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const settings = ref({})

export function getSettings() {
  // Fetch settings from server
  createResource({
    url: 'invite.invite.doctype.event_settings.event_settings.get_event_settings',
    cache: 'Event Settings',
    auto: true,
    onSuccess: (data) => {
      if (data) {
        settings.value = data
      }
    },
  })

  const brand = reactive({
    name: 'Invite',
  })

  return {
    settings,
    brand,
  }
}
