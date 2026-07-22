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

      <!-- WhatsApp Settings -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
            WhatsApp Integration
          </div>
        </h3>
        <p class="text-sm text-gray-500 mb-4">Configure WhatsApp Cloud API to send messages and invitation cards as media attachments automatically.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormControl label="WhatsApp Provider" type="select" v-model="form.whatsapp_provider" :options="whatsappProviderOptions" />
          <FormControl label="WhatsApp API Version" v-model="form.whatsapp_api_version" placeholder="v21.0" />
        </div>
        <FormControl label="WhatsApp API Access Token" type="password" v-model="form.whatsapp_api_key" class="mt-4" placeholder="EAAT..." />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <FormControl label="WhatsApp Phone Number ID" v-model="form.whatsapp_phone_number_id" placeholder="From Meta dashboard" />
          <FormControl label="WhatsApp Business Number" v-model="form.whatsapp_business_number" placeholder="+255712345678" />
        </div>
        <div class="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p class="text-xs text-amber-700">
            <strong>Setup required:</strong> You need a <a href="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started" target="_blank" class="underline">WhatsApp Cloud API</a> account from Meta. Get your Access Token and Phone Number ID from the Meta Developer Dashboard.
          </p>
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

const whatsappProviderOptions = [
  { label: 'Disabled', value: '' },
  { label: 'Meta API (WhatsApp Cloud API)', value: 'Meta API' },
  { label: 'Twilio', value: 'Twilio' },
]

const form = ref({
  default_currency: 'TZS',
  default_event_type: '',
  default_reminder_days: 3,
  app_name: 'Invite',
  app_logo: null,
  default_invitation_message: '',
  default_thank_you_template: '',
  whatsapp_provider: '',
  whatsapp_api_key: '',
  whatsapp_phone_number_id: '',
  whatsapp_business_number: '',
  whatsapp_api_version: 'v21.0',
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
        whatsapp_provider: settings.whatsapp_provider || '',
        whatsapp_api_key: settings.whatsapp_api_key || '',
        whatsapp_phone_number_id: settings.whatsapp_phone_number_id || '',
        whatsapp_business_number: settings.whatsapp_business_number || '',
        whatsapp_api_version: settings.whatsapp_api_version || 'v21.0',
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
