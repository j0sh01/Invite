import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const settings = ref({
  app_name: 'Invite',
  app_logo: null,
})

export function getSettings() {
  // Fetch settings from server
  createResource({
    url: 'invite.invite.doctype.event_settings.event_settings.get_event_settings',
    cache: 'Event Settings',
    auto: true,
    onSuccess: (data) => {
      if (data) {
        settings.value = data
        setupBrand()
      }
    },
  })

  function setupBrand() {
    brand.name = settings.value?.app_name || 'Invite'
    brand.logo = settings.value?.app_logo
  }

  const brand = reactive({
    name: 'Invite',
    logo: null,
  })

  return {
    settings,
    brand,
    setupBrand,
  }
}
