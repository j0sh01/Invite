<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p class="text-gray-500">Loading event...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="text-center p-8">
        <FeatherIcon name="alert-circle" class="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h2 class="text-lg font-semibold text-gray-900 mb-2">Event Not Found</h2>
        <p class="text-gray-500 text-sm">{{ error }}</p>
      </div>
    </div>

    <!-- Event Details -->
    <div v-else-if="event">
      <!-- Hero Image -->
      <div v-if="event.image" class="h-64 sm:h-80 bg-cover bg-center" :style="{ backgroundImage: `url(${event.image})` }">
        <div class="h-full bg-gradient-to-t from-black/60 to-transparent"></div>
      </div>
      <div v-else class="h-48 sm:h-64 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <FeatherIcon name="calendar" class="h-16 w-16 text-white opacity-30" />
      </div>

      <div class="max-w-3xl mx-auto px-4 -mt-16 relative z-10">
        <div class="bg-white rounded-xl shadow-lg p-6 sm:p-8">
          <!-- Event Title & Status -->
          <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
            <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">{{ event.event_name }}</h1>
            <span class="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700">
              {{ event.event_type || 'Event' }}
            </span>
          </div>

          <!-- Event Details -->
          <div class="space-y-4 mb-6">
            <div class="flex items-center gap-3 text-gray-600">
              <FeatherIcon name="calendar" class="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div>
                <p class="font-medium">{{ formatDate(event.event_date) }}</p>
                <p v-if="event.event_time" class="text-sm text-gray-500">{{ formatTime(event.event_time) }}</p>
              </div>
            </div>

            <div v-if="event.venue" class="flex items-center gap-3 text-gray-600">
              <FeatherIcon name="map-pin" class="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div>
                <p class="font-medium">{{ event.venue }}</p>
                <p v-if="event.location_address" class="text-sm text-gray-500">{{ event.location_address }}</p>
              </div>
            </div>

            <div v-if="event.organizer_name" class="flex items-center gap-3 text-gray-600">
              <FeatherIcon name="user" class="h-5 w-5 text-gray-400 flex-shrink-0" />
              <p>Organized by <span class="font-medium">{{ event.organizer_name }}</span></p>
            </div>
          </div>

          <!-- Description -->
          <div v-if="event.description" class="border-t pt-6 mb-6">
            <h3 class="text-sm font-medium text-gray-500 mb-2">About this Event</h3>
            <div class="text-gray-700 text-sm leading-relaxed" v-html="event.description"></div>
          </div>

          <!-- RSVP CTA -->
          <div class="border-t pt-6">
            <p class="text-sm text-gray-500 mb-4 text-center">Ready to respond to your invitation?</p>
            <button
              @click="goToRSVP"
              class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors text-center"
            >
              Respond to Invitation
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="max-w-3xl mx-auto px-4 py-8 text-center">
        <p class="text-xs text-gray-400">Powered by Invite - Event Management</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeRequest } from '@/utils/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const event = ref(null)

onMounted(async () => {
  const eventName = route.params.eventName
  if (!eventName) {
    error.value = 'Event not specified.'
    loading.value = false
    return
  }

  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get_public_event',
      params: { event: eventName },
    })
    if (data && data.event) {
      event.value = data.event
    } else {
      error.value = 'Event not found or is not publicly visible.'
    }
  } catch (e) {
    error.value = e.messages?.[0] || e.message || 'Failed to load event.'
  } finally {
    loading.value = false
  }
})

function goToRSVP() {
  // Navigate to RSVP page - guest will need their invite code
  router.push('/rsvp')
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

function formatTime(time) {
  if (!time) return ''
  const [hours, minutes] = time.split(':')
  const h = parseInt(hours)
  const ampm = h >= 12 ? 'PM' : 'AM'
  const h12 = h % 12 || 12
  return `${h12}:${minutes} ${ampm}`
}
</script>
