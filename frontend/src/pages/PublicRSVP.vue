<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Loading -->
      <div v-if="loading" class="bg-white rounded-xl shadow-lg p-8 text-center">
        <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p class="text-gray-500">Loading invitation...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="bg-white rounded-xl shadow-lg p-8 text-center">
        <FeatherIcon name="alert-circle" class="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h2 class="text-lg font-semibold text-gray-900 mb-2">Invalid Invitation</h2>
        <p class="text-gray-500 text-sm">{{ error }}</p>
      </div>

      <!-- Success -->
      <div v-else-if="submitted" class="bg-white rounded-xl shadow-lg p-8 text-center">
        <div class="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <FeatherIcon name="check" class="h-8 w-8 text-green-600" />
        </div>
        <h2 class="text-lg font-semibold text-gray-900 mb-2">{{ submitMessage }}</h2>
        <p class="text-gray-500 text-sm">Thank you for your response!</p>
      </div>

      <!-- RSVP Form -->
      <div v-else-if="invitation" class="bg-white rounded-xl shadow-lg overflow-hidden">
        <!-- Event Image -->
        <div v-if="invitation.event_image" class="h-40 bg-cover bg-center" :style="{ backgroundImage: `url(${invitation.event_image})` }"></div>
        <div v-else class="h-32 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <FeatherIcon name="calendar" class="h-12 w-12 text-white opacity-50" />
        </div>

        <div class="p-6">
          <h1 class="text-xl font-bold text-gray-900 mb-1">{{ invitation.event_name }}</h1>
          <p class="text-sm text-gray-500 mb-4">
            {{ formatDate(invitation.event_date) }}
            <span v-if="invitation.event_time"> at {{ invitation.event_time }}</span>
          </p>
          <p v-if="invitation.venue" class="text-sm text-gray-600 mb-4">
            <FeatherIcon name="map-pin" class="h-4 w-4 inline mr-1" />
            {{ invitation.venue }}
          </p>

          <div class="border-t pt-4 mt-4">
            <p class="text-sm font-medium text-gray-700 mb-3">Hello, <strong>{{ invitation.guest_name }}</strong></p>
            <p class="text-sm text-gray-500 mb-6">You are invited to this event. Please respond below:</p>

            <!-- RSVP Buttons -->
            <div class="grid grid-cols-3 gap-3 mb-6">
              <button
                @click="rsvpStatus = 'Accepted'"
                class="flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all"
                :class="rsvpStatus === 'Accepted' ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 hover:border-gray-300'"
              >
                <FeatherIcon name="check-circle" class="h-6 w-6" />
                <span class="text-sm font-medium">Accept</span>
              </button>
              <button
                @click="rsvpStatus = 'Declined'"
                class="flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all"
                :class="rsvpStatus === 'Declined' ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 hover:border-gray-300'"
              >
                <FeatherIcon name="x-circle" class="h-6 w-6" />
                <span class="text-sm font-medium">Decline</span>
              </button>
              <button
                @click="rsvpStatus = 'Maybe'"
                class="flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all"
                :class="rsvpStatus === 'Maybe' ? 'border-amber-500 bg-amber-50 text-amber-700' : 'border-gray-200 hover:border-gray-300'"
              >
                <FeatherIcon name="help-circle" class="h-6 w-6" />
                <span class="text-sm font-medium">Maybe</span>
              </button>
            </div>

            <!-- Number of Attendees -->
            <div v-if="rsvpStatus === 'Accepted' || rsvpStatus === 'Maybe'" class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Number of Attendees</label>
              <input
                v-model.number="numberOfAttendees"
                type="number"
                min="1"
                max="10"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <!-- Message -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-2">Message (optional)</label>
              <textarea
                v-model="message"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Any message for the organizer..."
              ></textarea>
            </div>

            <!-- Submit Button -->
            <button
              @click="submitRSVP"
              :disabled="!rsvpStatus || submitting"
              class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {{ submitting ? 'Submitting...' : 'Submit Response' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { frappeRequest } from '@/utils/api'

const route = useRoute()

const loading = ref(true)
const error = ref('')
const invitation = ref(null)
const rsvpStatus = ref('')
const numberOfAttendees = ref(1)
const message = ref('')
const submitting = ref(false)
const submitted = ref(false)
const submitMessage = ref('')

onMounted(async () => {
  const code = route.query.code
  if (!code) {
    error.value = 'No invitation code provided.'
    loading.value = false
    return
  }

  try {
    const data = await frappeRequest({
      url: 'invite.api.rsvp.get_invitation_by_code',
      params: { code },
    })
    if (data && data.invitation) {
      invitation.value = data.invitation
    } else {
      error.value = 'Invitation not found or expired.'
    }
  } catch (e) {
    error.value = e.messages?.[0] || e.message || 'Failed to load invitation.'
  } finally {
    loading.value = false
  }
})

async function submitRSVP() {
  if (!rsvpStatus.value) return
  submitting.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.api.rsvp.submit_rsvp',
      params: {
        code: route.query.code,
        status: rsvpStatus.value,
        attendees: numberOfAttendees.value,
        message: message.value,
      },
    })
    submitted.value = true
    submitMessage.value = rsvpStatus.value === 'Accepted'
      ? `Thank you, ${invitation.value.guest_name}. Your attendance has been confirmed.`
      : rsvpStatus.value === 'Declined'
        ? `Thank you for letting us know, ${invitation.value.guest_name}.`
        : `Thank you, ${invitation.value.guest_name}. We'll keep you updated.`
  } catch (e) {
    alert(e.messages?.[0] || e.message || 'Failed to submit response. Please try again.')
  } finally {
    submitting.value = false
  }
}

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>
