<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-2xl font-semibold text-gray-900 mb-6">Settings</h1>

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading settings...</div>

    <div v-else class="space-y-6">
      <!-- General Settings -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">General Settings</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormControl label="Default Currency" type="select" v-model="form.default_currency" :options="currencyOptions" />
          <FormControl label="Default Event Type" type="select" v-model="form.default_event_type" :options="eventTypeOptions" />
        </div>
        <FormControl label="Default Reminder Days Before" type="number" v-model="form.default_reminder_days" class="mt-4" />
      </div>

      <!-- Branding -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">Branding</h3>
        <FormControl label="App Name" v-model="form.app_name" />
        <div class="mt-4">
          <label class="block text-sm text-gray-700 mb-2">App Logo</label>
          <div class="flex items-center gap-4">
            <div v-if="form.app_logo" class="h-16 w-16 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden">
              <img :src="form.app_logo" class="h-full w-full object-cover" />
            </div>
            <div v-else class="h-16 w-16 rounded-lg bg-gray-100 flex items-center justify-center">
              <FeatherIcon name="image" class="h-6 w-6 text-gray-400" />
            </div>
            <Button variant="ghost">Upload Logo</Button>
          </div>
        </div>
      </div>

      <!-- Default Messages -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">Default Messages</h3>
        <FormControl label="Default Invitation Message" type="textarea" v-model="form.default_invitation_message" />
        <FormControl label="Default Thank You Template" type="textarea" v-model="form.default_thank_you_template" class="mt-4" />
      </div>

      <!-- Save Button -->
      <div class="flex justify-end">
        <Button @click="saveSettings" variant="solid" :loading="saving">Save Settings</Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { frappeRequest } from '@/utils/api'
import { useNotifications } from '@/composables/notifications'

const { showToast } = useNotifications()

const loading = ref(true)
const saving = ref(false)
const eventTypes = ref([])

const form = ref({
  default_currency: 'TZS',
  default_event_type: '',
  default_reminder_days: 3,
  app_name: 'Invite',
  app_logo: null,
  default_invitation_message: '',
  default_thank_you_template: '',
})

const currencyOptions = [
  { label: 'TZS (Tanzanian Shilling)', value: 'TZS' },
  { label: 'USD (US Dollar)', value: 'USD' },
  { label: 'KES (Kenyan Shilling)', value: 'KES' },
  { label: 'UGX (Ugandan Shilling)', value: 'UGX' },
  { label: 'EUR (Euro)', value: 'EUR' },
]

const eventTypeOptions = computed(() => {
  return [{ label: 'None', value: '' }, ...(eventTypes.value || []).map(t => ({ label: t.event_type_name, value: t.event_type_name }))]
})

onMounted(async () => {
  try {
    const [settings, types] = await Promise.all([
      frappeRequest({ url: 'invite.invite.doctype.event_settings.event_settings.get_event_settings' }),
      frappeRequest({ url: 'frappe.client.get_list', params: { doctype: 'Event Type', fields: ['event_type_name'] } }),
    ])
    eventTypes.value = types || []
    if (settings) {
      form.value = {
        default_currency: settings.default_currency || 'TZS',
        default_event_type: settings.default_event_type || '',
        default_reminder_days: settings.default_reminder_days || 3,
        app_name: settings.app_name || 'Invite',
        app_logo: settings.app_logo || null,
        default_invitation_message: settings.default_invitation_message || '',
        default_thank_you_template: settings.default_thank_you_template || '',
      }
    }
  } catch (e) {
    console.error('Failed to load settings:', e)
  } finally {
    loading.value = false
  }
})

async function saveSettings() {
  saving.value = true
  try {
    await frappeRequest({
      url: 'frappe.client.save',
      params: {
        doc: JSON.stringify({
          doctype: 'Event Settings',
          name: 'Event Settings',
          ...form.value,
        }),
      },
    })
    showToast('Settings saved successfully!', 'success')
  } catch (e) {
    console.error('Failed to save settings:', e)
  } finally {
    saving.value = false
  }
}
</script>
