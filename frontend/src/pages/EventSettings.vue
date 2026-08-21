<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-xl sm:text-2xl font-semibold text-gray-900 mb-6">Event Settings</h1>

    <!-- Sub-navigation Tabs -->
    <EventTabs :eventId="props.eventId" />

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading event settings...</div>

    <div v-else class="bg-white rounded-lg border p-6">
      <div class="space-y-6">
        <div>
          <h3 class="text-base font-medium text-gray-900 mb-4">Event Details</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Event Name" v-model="form.event_name" required />
            <FormControl label="Event Type" type="select" v-model="form.event_type" :options="eventTypeOptions" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <FormControl label="Status" type="select" v-model="form.event_status" :options="eventStatusOptions" />
            <div></div>
          </div>
        </div>

        <div class="border-t pt-6">
          <h3 class="text-base font-medium text-gray-900 mb-4">Date & Location</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Event Date" type="date" v-model="form.event_date" />
            <FormControl label="Event Time" type="time" v-model="form.event_time" />
          </div>
          <FormControl label="Venue" v-model="form.venue" class="mt-4" />
          <FormControl label="Address" type="textarea" v-model="form.location_address" class="mt-4" />
        </div>

        <div class="border-t pt-6">
          <h3 class="text-base font-medium text-gray-900 mb-4">Organizer</h3>
          <FormControl label="Organizer Name" v-model="form.organizer_name" />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <FormControl label="Contact" v-model="form.organizer_contact" />
            <FormControl label="Email" v-model="form.organizer_email" />
          </div>
          <FormControl label="Max Guests" type="number" v-model="form.max_guests" class="mt-4" />
        </div>

        <div class="border-t pt-6">
          <h3 class="text-base font-medium text-gray-900 mb-4">Event Image</h3>
          <div class="flex flex-col sm:flex-row items-start gap-4 sm:gap-6">
            <div class="flex-shrink-0">
              <div
                class="w-32 h-32 rounded-lg border bg-gray-50 flex items-center justify-center overflow-hidden cursor-pointer hover:bg-gray-100 transition-colors"
                @click="triggerImageInput"
              >
                <img v-if="form.image" :src="form.image" class="w-full h-full object-cover" />
                <div v-else class="text-center p-2">
                  <FeatherIcon name="image" class="h-8 w-8 mx-auto text-gray-400" />
                  <p class="text-xs text-gray-400 mt-1">Click to upload</p>
                </div>
              </div>
              <input ref="imageInput" type="file" accept="image/*" class="hidden" @change="handleImageUpload" />
            </div>
            <div class="text-sm text-gray-500">
              <p>Upload an event image/photo for invitation cards and communications.</p>
              <p class="mt-1">Recommended size: 1200x600px</p>
            </div>
          </div>
        </div>

        <div class="border-t pt-6">
          <h3 class="text-base font-medium text-gray-900 mb-4">Configuration</h3>
          <FormControl label="Currency" type="select" v-model="form.currency" :options="currencyOptions" class="w-full sm:w-48" />
          <div class="flex flex-wrap items-center gap-4 sm:gap-6 mt-4">
            <FormControl type="checkbox" label="Enable Reminders" v-model="form.enable_reminders" />
            <FormControl type="checkbox" label="Enable Public RSVP" v-model="form.enable_public_rsvp" />
          </div>
          <div class="mt-4">
            <FormControl label="Reminder Days Before" type="number" v-model="form.reminder_days_before" class="w-full sm:w-48" />
          </div>
        </div>

        <div class="border-t pt-6">
          <h3 class="text-base font-medium text-gray-900 mb-4">Send Communications</h3>
          <p class="text-sm text-gray-500 mb-4">Manually trigger reminders and communications to guests.</p>
          
          <!-- Reminder Results -->
          <div v-if="reminderResult" class="mb-4 rounded-lg p-4" :class="reminderResult.total_failed ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'">
            <div class="flex items-center gap-2 mb-2">
              <FeatherIcon :name="reminderResult.total_failed ? 'alert-triangle' : 'check-circle'" 
                :class="reminderResult.total_failed ? 'text-amber-500' : 'text-green-500'" class="h-5 w-5" />
              <span class="text-sm font-medium" :class="reminderResult.total_failed ? 'text-amber-800' : 'text-green-800'">
                {{ reminderResult.total_sent || 0 }} sent, {{ reminderResult.total_failed || 0 }} failed
              </span>
            </div>
            <div v-if="reminderResult.failed?.length" class="text-xs text-red-600 space-y-1 max-h-20 overflow-y-auto">
              <p v-for="f in reminderResult.failed" :key="f.guest + (f.error || '')">{{ f.guest }}: {{ f.error }}</p>
            </div>
          </div>

          <div class="flex flex-col sm:flex-row items-start sm:items-end gap-3">
            <FormControl
              label="Communication Type"
              type="select"
              v-model="selectedReminderType"
              :options="reminderTypeOptions"
              class="w-full sm:w-52"
            />
            <FormControl
              label="Channel"
              type="select"
              v-model="selectedReminderChannel"
              :options="reminderChannelOptions"
              class="w-full sm:w-44"
            />
            <Button
              @click="triggerReminder(selectedReminderChannel, selectedReminderType)"
              variant="solid"
              size="sm"
              :loading="reminderLoading"
              iconLeft="send"
              :label="__('Send')"
              class="mb-0.5"
            />
          </div>
        </div>

        <div class="border-t pt-6">
          <FormControl label="Description" type="textarea" v-model="form.description" />
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-8 pt-6 border-t">
        <Button @click="$router.back()" variant="ghost">Cancel</Button>
        <Button @click="saveSettings" variant="solid" :loading="saving">Save Changes</Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'

const props = defineProps({ eventId: String })
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const eventTypes = ref([])
const eventStatuses = ref([])
const imageInput = ref(null)
const uploadingImage = ref(false)
const reminderResult = ref(null)
const reminderLoading = ref(false)
const selectedReminderType = ref('event')
const selectedReminderChannel = ref('WhatsApp')

const reminderTypeOptions = [
  { label: __('Event Reminder'), value: 'event' },
  { label: __('Thank You'), value: 'thank_you' },
]

const reminderChannelOptions = [
  { label: __('WhatsApp'), value: 'WhatsApp' },
  { label: __('Email'), value: 'Email' },
]

const form = ref({
  event_name: '',
  event_type: '',
  event_status: '',
  event_date: '',
  event_time: '',
  venue: '',
  location_address: '',
  organizer_name: '',
  organizer_contact: '',
  organizer_email: '',
  max_guests: 0,
  currency: 'TZS',
  enable_reminders: 1,
  enable_public_rsvp: 0,
  reminder_days_before: 3,
  image: '',
  description: '',
})

const eventTypeOptions = computed(() => 
  (eventTypes.value || []).map(t => ({ label: t.event_type_name, value: t.event_type_name }))
)

const eventStatusOptions = computed(() =>
  (eventStatuses.value || []).map(s => ({ label: s.status_name, value: s.status_name }))
)

const currencyOptions = [
  { label: 'TZS', value: 'TZS' },
  { label: 'USD', value: 'USD' },
  { label: 'KES', value: 'KES' },
  { label: 'UGX', value: 'UGX' },
  { label: 'EUR', value: 'EUR' },
]

onMounted(async () => {
  await Promise.all([loadEvent(), loadOptions()])
})

async function loadEvent() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get',
      params: { event: props.eventId },
    })
    const e = data.event
    if (e) {
      form.value = {
        event_name: e.event_name || '',
        event_type: e.event_type || '',
        event_status: e.event_status || 'Planning',
        event_date: e.event_date || '',
        event_time: e.event_time || '',
        venue: e.venue || '',
        location_address: e.location_address || '',
        organizer_name: e.organizer_name || '',
        organizer_contact: e.organizer_contact || '',
        organizer_email: e.organizer_email || '',
        max_guests: e.max_guests || 0,
        currency: e.currency || 'TZS',
        enable_reminders: e.enable_reminders ? 1 : 0,
        enable_public_rsvp: e.enable_public_rsvp ? 1 : 0,
        reminder_days_before: e.reminder_days_before || 3,
        image: e.image || '',
        description: e.description || '',
      }
    }
  } catch (e) {
    console.error('Failed to load event:', e)
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [types, statuses] = await Promise.all([
      frappeRequest({ url: 'frappe.client.get_list', params: { doctype: 'Event Type', fields: ['event_type_name'] } }),
      frappeRequest({ url: 'frappe.client.get_list', params: { doctype: 'Event Status', fields: ['status_name'] } }),
    ])
    eventTypes.value = types || []
    eventStatuses.value = statuses || []
  } catch (e) {
    console.error('Failed to load options:', e)
  }
}

function triggerImageInput() {
  imageInput.value?.click()
}

async function triggerReminder(channel, type) {
  reminderLoading.value = true
  reminderResult.value = null
  try {
    const result = await frappeRequest({
      url: 'invite.api.card.send_reminders',
      params: { event: props.eventId, channel, reminder_type: type },
    })
    reminderResult.value = result || { total_sent: 0, total_failed: 0, sent: [], failed: [] }
  } catch (e) {
    console.error('Failed to send reminders:', e)
    reminderResult.value = { total_sent: 0, total_failed: 1, sent: [], failed: [{ guest: 'N/A', error: e.message || 'Failed' }] }
  } finally {
    reminderLoading.value = false
  }
}

async function handleImageUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploadingImage.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doctype', 'Event')
    formData.append('docname', props.eventId)
    formData.append('is_private', '0')

    const res = await fetch('/api/method/upload_file', {
      method: 'POST',
      headers: {
        'X-Frappe-CSRF-Token': window.csrf_token || '',
        'X-Frappe-Site-Name': window.location.hostname,
      },
      body: formData,
    })
    const data = await res.json()
    if (data.message?.file_url) {
      form.value.image = data.message.file_url
    }
  } catch (e) {
    console.error('Failed to upload image:', e)
  } finally {
    uploadingImage.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await frappeRequest({
      url: 'invite.api.event.update',
      params: {
        event: props.eventId,
        data: JSON.stringify(form.value),
      },
    })
    router.push(`/events/${props.eventId}`)
  } catch (e) {
    console.error('Failed to save event settings:', e)
  } finally {
    saving.value = false
  }
}
</script>
