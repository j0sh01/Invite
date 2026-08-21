<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-xl sm:text-2xl font-semibold text-gray-900 mb-6">Settings</h1>

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
        <p class="text-sm text-gray-500 mb-4">Configure WhatsApp provider to send messages and invitation cards automatically.</p>
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

      <!-- Twilio Settings -->
      <div v-if="form.whatsapp_provider === 'Twilio'" class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">
          <div class="flex items-center gap-2">
            <FeatherIcon name="phone" class="h-5 w-5 text-red-500" />
            Twilio Settings
          </div>
        </h3>
        <p class="text-sm text-gray-500 mb-4">Configure Twilio for WhatsApp messaging using the Content API (Content Template Builder).</p>
        <FormControl label="Twilio Account SID" v-model="form.twilio_account_sid" placeholder="AC..." class="mb-4" />
        <FormControl label="Twilio Auth Token" type="password" v-model="form.twilio_auth_token" class="mb-4" />
        <FormControl label="Twilio WhatsApp Number" v-model="form.twilio_whatsapp_number" placeholder="+14155238886" />

        <!-- Test Connection -->
        <div class="mt-4">
          <div class="flex items-center gap-3">
            <Button @click="testTwilioConnection" variant="ghost" size="sm" :loading="twilioTesting" iconLeft="check-circle" label="Test Connection" />
          </div>
          <div v-if="twilioTestResult" class="mt-3 rounded-lg p-4 text-sm" :class="twilioTestResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
            <div class="flex items-center gap-2 mb-1">
              <FeatherIcon :name="twilioTestResult.success ? 'check-circle' : 'alert-triangle'" class="h-4 w-4 flex-shrink-0" :class="twilioTestResult.success ? 'text-green-500' : 'text-red-500'" />
              <span class="font-medium" :class="twilioTestResult.success ? 'text-green-800' : 'text-red-800'">
                {{ twilioTestResult.success ? 'Connected — ' + twilioTestResult.account_name : 'Connection Failed' }}
              </span>
            </div>
            <p class="text-xs mt-1" :class="twilioTestResult.success ? 'text-green-600' : 'text-red-600'">{{ twilioTestResult.error || twilioTestResult.message }}</p>
            <div v-if="twilioTestResult.diagnostics" class="mt-2 text-xs text-gray-500 space-y-0.5">
              <p v-if="twilioTestResult.diagnostics.account_sid_masked">SID: {{ twilioTestResult.diagnostics.account_sid_masked }}</p>
              <p v-if="twilioTestResult.diagnostics.auth_token_length !== undefined">Auth Token: {{ twilioTestResult.diagnostics.auth_token_length > 0 ? '✓ set (' + twilioTestResult.diagnostics.auth_token_length + ' chars)' : '✗ empty' }}</p>
              <p v-if="twilioTestResult.diagnostics.whatsapp_number">WhatsApp Number: {{ twilioTestResult.diagnostics.whatsapp_number }}</p>
            </div>
          </div>
        </div>

        <div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-xs text-blue-700">
            <strong>Content API:</strong> Use Twilio's <a href="https://www.twilio.com/console/sms/content-templates" target="_blank" class="underline">Content Template Builder</a> to create message templates. Templates are referenced by SID when sending messages.
          </p>
        </div>

        <!-- Template SIDs -->
        <div class="mt-6 border-t pt-4">
          <h4 class="text-sm font-medium text-gray-900 mb-3">Content Template SIDs</h4>
          <p class="text-xs text-gray-500 mb-4">Paste the Content SID from each template in Twilio's Content Template Builder. Leave blank to send plain text fallback.</p>
          <div class="space-y-3">
            <FormControl label="Event Invitation" v-model="form.twilio_template_invitation" placeholder="HX..." />
            <FormControl label="RSVP Confirmation" v-model="form.twilio_template_rsvp_confirm" placeholder="HX..." />
            <FormControl label="RSVP Reminder" v-model="form.twilio_template_rsvp_reminder" placeholder="HX..." />
            <FormControl label="Event Reminder" v-model="form.twilio_template_event_reminder" placeholder="HX..." />
            <FormControl label="Event Update" v-model="form.twilio_template_event_update" placeholder="HX..." />
            <FormControl label="QR / Check-in" v-model="form.twilio_template_qr_checkin" placeholder="HX..." />
            <FormControl label="Thank You" v-model="form.twilio_template_thank_you" placeholder="HX..." />
          </div>

          <!-- Fetch Templates Button -->
          <div class="mt-4 flex items-center gap-3">
            <Button @click="fetchContentTemplates" variant="ghost" size="sm" :loading="fetchingTemplates" iconLeft="refresh-cw" label="Fetch My Templates" />
          </div>
          <div v-if="contentTemplates.length" class="mt-3 bg-gray-50 rounded-lg p-3 text-xs max-h-48 overflow-y-auto">
            <p class="font-medium text-gray-700 mb-2">Available Templates from Twilio:</p>
            <div v-for="t in contentTemplates" :key="t.sid" class="flex items-center justify-between py-1 border-b border-gray-200 last:border-0">
              <span class="text-gray-700">{{ t.friendly_name || t.sid }}</span>
              <span class="text-gray-400 font-mono text-xs">{{ t.sid }}</span>
            </div>
          </div>
        </div>

        <!-- Send Test Message -->
        <div class="mt-6 border-t pt-4">
          <h4 class="text-sm font-medium text-gray-900 mb-3">Send Test Message</h4>
          <p class="text-xs text-gray-500 mb-4">Send a test WhatsApp message to verify everything works. In sandbox mode, messages arrive on your WhatsApp.</p>
          <div class="flex flex-col sm:flex-row items-start sm:items-end gap-3">
            <FormControl label="Your WhatsApp Number" v-model="testPhoneNumber" placeholder="e.g. +255712345678" class="w-full sm:w-64" />
            <FormControl label="Template (optional)" type="select" v-model="testTemplateSid" :options="testTemplateOptions" class="w-full sm:w-56" />
            <Button @click="sendTestMessage" variant="solid" size="sm" :loading="sendingTest" iconLeft="send" label="Send Test" class="mb-0.5" />
          </div>
          <div v-if="testSendResult" class="mt-3 rounded-lg p-3 text-sm" :class="testSendResult.success ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'">
            {{ testSendResult.success ? '✓ ' + testSendResult.message : '✗ ' + testSendResult.error }}
          </div>
        </div>
      </div>

      <!-- QR Code Settings -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">
          <div class="flex items-center gap-2">
            <FeatherIcon name="smartphone" class="h-5 w-5 text-purple-500" />
            QR Code Settings
          </div>
        </h3>
        <p class="text-sm text-gray-500 mb-4">Customize the appearance of QR codes on invitation cards.</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm text-gray-700 mb-2">Foreground Color</label>
            <input type="color" v-model="form.qr_code_foreground_color" class="w-full h-10 rounded border border-gray-300 cursor-pointer" />
          </div>
          <div>
            <label class="block text-sm text-gray-700 mb-2">Background Color</label>
            <input type="color" v-model="form.qr_code_background_color" class="w-full h-10 rounded border border-gray-300 cursor-pointer" />
          </div>
          <FormControl label="QR Code Size (px)" type="number" v-model="form.qr_code_size" />
        </div>
      </div>

      <!-- Google Calendar Settings -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">
          <div class="flex items-center gap-2">
            <FeatherIcon name="calendar" class="h-5 w-5 text-blue-500" />
            Google Calendar Integration
          </div>
        </h3>
        <p class="text-sm text-gray-500 mb-4">Connect Google Calendar to sync events and send calendar invites to guests.</p>
        <FormControl label="Google Client ID" v-model="form.google_client_id" placeholder="From Google Cloud Console" />
        <div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-xs text-blue-700">
            <strong>Setup required:</strong> Create OAuth 2.0 credentials in the <a href="https://console.cloud.google.com/apis/credentials" target="_blank" class="underline">Google Cloud Console</a> and enable the Google Calendar API.
          </p>
        </div>
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

// Twilio test state
const twilioTesting = ref(false)
const twilioTestResult = ref(null)
const testPhoneNumber = ref('')
const testTemplateSid = ref('')
const testSendResult = ref(null)
const sendingTest = ref(false)
const contentTemplates = ref([])
const fetchingTemplates = ref(false)

const whatsappProviderOptions = [
  { label: 'Disabled', value: '' },
  { label: 'Official WhatsApp API (Meta Cloud API)', value: 'Official WhatsApp API' },
  { label: 'Twilio', value: 'Twilio' },
]

const testTemplateOptions = computed(() => {
  const opts = [{ label: 'Plain Text (no template)', value: '' }]
  for (const t of contentTemplates.value) {
    opts.push({ label: t.friendly_name || t.sid, value: t.sid })
  }
  return opts
})

const form = ref({
  default_currency: 'TZS',
  default_event_type: '',
  default_reminder_days: 3,
  qr_code_foreground_color: '#000000',
  qr_code_background_color: '#FFFFFF',
  qr_code_size: 8,
  whatsapp_provider: '',
  whatsapp_api_key: '',
  whatsapp_phone_number_id: '',
  whatsapp_business_number: '',
  whatsapp_api_version: 'v21.0',
  twilio_account_sid: '',
  twilio_auth_token: '',
  twilio_whatsapp_number: '',
  twilio_template_invitation: '',
  twilio_template_rsvp_confirm: '',
  twilio_template_rsvp_reminder: '',
  twilio_template_event_reminder: '',
  twilio_template_event_update: '',
  twilio_template_qr_checkin: '',
  twilio_template_thank_you: '',
  google_client_id: '',
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
        qr_code_foreground_color: settings.qr_code_foreground_color || '#000000',
        qr_code_background_color: settings.qr_code_background_color || '#FFFFFF',
        qr_code_size: settings.qr_code_size || 8,
        whatsapp_provider: settings.whatsapp_provider || '',
        whatsapp_api_key: settings.whatsapp_api_key || '',
        whatsapp_phone_number_id: settings.whatsapp_phone_number_id || '',
        whatsapp_business_number: settings.whatsapp_business_number || '',
        whatsapp_api_version: settings.whatsapp_api_version || 'v21.0',
        twilio_account_sid: settings.twilio_account_sid || '',
        twilio_auth_token: settings.twilio_auth_token || '',
        twilio_whatsapp_number: settings.twilio_whatsapp_number || '',
        twilio_template_invitation: settings.twilio_template_invitation || '',
        twilio_template_rsvp_confirm: settings.twilio_template_rsvp_confirm || '',
        twilio_template_rsvp_reminder: settings.twilio_template_rsvp_reminder || '',
        twilio_template_event_reminder: settings.twilio_template_event_reminder || '',
        twilio_template_event_update: settings.twilio_template_event_update || '',
        twilio_template_qr_checkin: settings.twilio_template_qr_checkin || '',
        twilio_template_thank_you: settings.twilio_template_thank_you || '',
        google_client_id: settings.google_client_id || '',
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
      url: 'invite.invite.doctype.event_settings.event_settings.save_event_settings',
      params: form.value,
    })
    showToast('Settings saved successfully!', 'success', 3000)
  } catch (e) {
    console.error('Failed to save settings:', e)
  } finally {
    saving.value = false
  }
}

async function testTwilioConnection() {
  twilioTesting.value = true
  twilioTestResult.value = null
  try {
    // Save settings first so the test uses latest credentials
    await frappeRequest({
      url: 'invite.invite.doctype.event_settings.event_settings.save_event_settings',
      params: form.value,
    })
    const result = await frappeRequest({
      url: 'invite.api.twilio.test_connection',
    })
    twilioTestResult.value = result
    if (result.success) {
      showToast('Twilio connected successfully!', 'success', 3000)
    }
  } catch (e) {
    twilioTestResult.value = { success: false, error: e.message || 'Connection test failed' }
  } finally {
    twilioTesting.value = false
  }
}

async function fetchContentTemplates() {
  fetchingTemplates.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.api.twilio.list_content_templates',
    })
    contentTemplates.value = result || []
    if (result.length) {
      showToast(`Found ${result.length} templates`, 'success', 3000)
    } else {
      showToast('No templates found. Create templates in Twilio Content Template Builder.', 'info', 4000)
    }
  } catch (e) {
    console.error('Failed to fetch templates:', e)
    showToast('Failed to fetch templates', 'error', 3000)
  } finally {
    fetchingTemplates.value = false
  }
}

async function sendTestMessage() {
  if (!testPhoneNumber.value) {
    showToast('Enter your WhatsApp number first', 'error', 3000)
    return
  }
  sendingTest.value = true
  testSendResult.value = null
  try {
    // Save settings first
    await frappeRequest({
      url: 'invite.invite.doctype.event_settings.event_settings.save_event_settings',
      params: form.value,
    })
    const result = await frappeRequest({
      url: 'invite.api.twilio.send_test_message',
      params: {
        to_number: testPhoneNumber.value,
        template_sid: testTemplateSid.value || null,
        message: null,
      },
    })
    testSendResult.value = result
    if (result.success) {
      showToast('Test message sent! Check your WhatsApp.', 'success', 5000)
    }
  } catch (e) {
    testSendResult.value = { success: false, error: e.message || 'Failed to send test message' }
  } finally {
    sendingTest.value = false
  }
}
</script>
