<template>
  <div v-if="loading" class="text-center py-12 text-gray-500">Loading event details...</div>

  <div v-else-if="event" class="max-w-7xl mx-auto">
    <!-- Event Header -->
    <div class="bg-white rounded-lg border p-4 sm:p-6 mb-6">
      <div class="flex flex-col sm:flex-row items-start justify-between gap-4">
        <div class="w-full sm:w-auto">
          <div class="flex flex-wrap items-center gap-2 mb-2">
            <h1 class="text-xl sm:text-2xl font-semibold text-gray-900 truncate">{{ event.event_name }}</h1>
            <span :class="statusClass(event.event_status)" class="text-xs px-2 py-1 rounded-full font-medium whitespace-nowrap">
              {{ event.event_status }}
            </span>
          </div>
          <div class="text-sm text-gray-500 space-y-1">
            <p v-if="event.event_type">Type: {{ event.event_type }}</p>
            <p v-if="event.event_date">
              <FeatherIcon name="calendar" class="h-3.5 w-3.5 inline mr-1" />
              {{ formatDate(event.event_date) }}
              <span v-if="event.event_time"> at {{ event.event_time }}</span>
            </p>
            <p v-if="event.venue">
              <FeatherIcon name="map-pin" class="h-3.5 w-3.5 inline mr-1" />
              {{ event.venue }}
            </p>
            <p v-if="event.organizer_name">Organizer: {{ event.organizer_name }}</p>
          </div>
        </div>
        <div class="flex gap-2 self-end sm:self-start">
          <Button @click="$router.push(`/events/${props.eventId}/settings`)" variant="ghost" size="xs">
            <FeatherIcon name="edit-2" class="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>

    <!-- Event Stats Cards (Responsive) -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-8 gap-2 sm:gap-3 mb-6">
      <div class="bg-white rounded-lg border p-2 sm:p-3 text-center">
        <p class="text-base sm:text-lg font-semibold text-gray-900">{{ event.total_guests || 0 }}</p>
        <p class="text-xs text-gray-500">Total Guests</p>
      </div>
      <div class="bg-white rounded-lg border p-2 sm:p-3 text-center">
        <p class="text-base sm:text-lg font-semibold text-blue-600">{{ event.total_invited || 0 }}</p>
        <p class="text-xs text-gray-500">Invited</p>
      </div>
      <div class="bg-white rounded-lg border p-2 sm:p-3 text-center">
        <p class="text-base sm:text-lg font-semibold text-indigo-600">{{ event.total_rsvped || 0 }}</p>
        <p class="text-xs text-gray-500">RSVPed</p>
      </div>
      <div class="bg-white rounded-lg border p-2 sm:p-3 text-center">
        <p class="text-base sm:text-lg font-semibold text-green-600">{{ event.total_accepted || 0 }}</p>
        <p class="text-xs text-gray-500">Accepted</p>
      </div>
      <div class="bg-white rounded-lg border p-2 sm:p-3 text-center">
        <p class="text-base sm:text-lg font-semibold text-red-600">{{ event.total_declined || 0 }}</p>
        <p class="text-xs text-gray-500">Declined</p>
      </div>
      <div class="bg-white rounded-lg border p-2 sm:p-3 text-center">
        <p class="text-base sm:text-lg font-semibold text-amber-600">{{ event.total_checked_in || 0 }}</p>
        <p class="text-xs text-gray-500">Checked In</p>
      </div>
    </div>

    <!-- Sub-navigation Tabs -->
    <EventTabs :eventId="props.eventId" />

    <!-- Quick stats for overview tab -->
    <div v-if="isOverviewTab" class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="bg-white rounded-lg border p-4 sm:p-5 hover:shadow-md cursor-pointer transition-shadow" @click="$router.push(`/events/${props.eventId}/guests`)">
        <FeatherIcon name="users" class="h-6 w-6 sm:h-8 sm:w-8 text-blue-500 mb-2 sm:mb-3" />
        <h4 class="text-sm font-medium text-gray-900">Guests</h4>
        <p class="text-xs text-gray-500 mt-1">Manage and import guests</p>
      </div>
      <div class="bg-white rounded-lg border p-4 sm:p-5 hover:shadow-md cursor-pointer transition-shadow" @click="$router.push(`/events/${props.eventId}/invitations`)">
        <FeatherIcon name="mail" class="h-6 w-6 sm:h-8 sm:w-8 text-green-500 mb-2 sm:mb-3" />
        <h4 class="text-sm font-medium text-gray-900">Invitations</h4>
        <p class="text-xs text-gray-500 mt-1">Send and track invitations</p>
      </div>
      <div class="bg-white rounded-lg border p-4 sm:p-5 hover:shadow-md cursor-pointer transition-shadow" @click="$router.push(`/events/${props.eventId}/checkin`)">
        <FeatherIcon name="camera" class="h-6 w-6 sm:h-8 sm:w-8 text-purple-500 mb-2 sm:mb-3" />
        <h4 class="text-sm font-medium text-gray-900">Check-In</h4>
        <p class="text-xs text-gray-500 mt-1">Scan QR codes for entry</p>
      </div>
    </div>

    <!-- Recent Activity (overview only) -->
    <div v-if="isOverviewTab" class="bg-white rounded-lg border">
      <div class="px-4 sm:px-6 py-4 border-b">
        <h3 class="text-sm sm:text-base font-medium text-gray-900">Recent Check-Ins</h3>
      </div>
      <div class="divide-y">
        <div v-for="ci in recentCheckins" :key="ci.name" class="px-4 sm:px-6 py-3 flex items-center justify-between text-sm">
          <div class="flex items-center gap-2">
            <FeatherIcon :name="ci.is_duplicate ? 'alert-circle' : 'check-circle'" 
              :class="ci.is_duplicate ? 'text-amber-500' : 'text-green-500'" class="h-4 w-4" />
            <span class="text-gray-900">{{ ci.guest_name }}</span>
          </div>
          <span class="text-gray-500 text-xs">{{ ci.checked_in_at ? formatDateTime(ci.checked_in_at) : '' }}</span>
        </div>
        <div v-if="!recentCheckins.length" class="px-4 sm:px-6 py-8 text-center text-gray-500 text-sm">
          No check-ins yet
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'

const props = defineProps({ eventId: String })
const route = useRoute()
const router = useRouter()
const event = ref(null)
const recentCheckins = ref([])
const loading = ref(true)

const isOverviewTab = computed(() => {
  return route.path === `/events/${props.eventId}` || route.path === `/events/${props.eventId}/`
})

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get',
      params: { event: props.eventId },
    })
    event.value = data.event
    recentCheckins.value = data.recent_checkins || []
  } catch (e) {
    console.error('Failed to load event:', e)
  } finally {
    loading.value = false
  }
})

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString()
}

function formatCurrency(amount) {
  if (!amount) return 'TZS 0'
  return `TZS ${Number(amount).toLocaleString()}`
}

function statusClass(status) {
  const classes = {
    'Planning': 'bg-blue-50 text-blue-700',
    'Invitations Sent': 'bg-orange-50 text-orange-700',
    'RSVPs Open': 'bg-purple-50 text-purple-700',
    'Ongoing': 'bg-yellow-50 text-yellow-700',
    'Completed': 'bg-green-50 text-green-700',
    'Cancelled': 'bg-red-50 text-red-700',
  }
  return classes[status] || 'bg-gray-50 text-gray-700'
}
</script>
