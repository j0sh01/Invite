<template>
  <div class="max-w-7xl mx-auto">
    <!-- Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-8">
      <div class="bg-white rounded-lg border p-5">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-blue-50">
            <FeatherIcon name="calendar" class="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p class="text-sm text-gray-500">Total Events</p>
            <p class="text-2xl font-semibold text-gray-900">{{ stats.total_events || 0 }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border p-5">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-green-50">
            <FeatherIcon name="trending-up" class="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p class="text-sm text-gray-500">Upcoming</p>
            <p class="text-2xl font-semibold text-gray-900">{{ stats.upcoming || 0 }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border p-5">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-purple-50">
            <FeatherIcon name="users" class="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p class="text-sm text-gray-500">Total Guests</p>
            <p class="text-2xl font-semibold text-gray-900">{{ stats.total_guests || 0 }}</p>
          </div>
        </div>
      </div>

    </div>

    <!-- Upcoming Events -->
    <div class="bg-white rounded-lg border mb-8">
      <div class="flex items-center justify-between px-6 py-4 border-b">
        <h3 class="text-base font-medium text-gray-900">Upcoming Events</h3>
        <Button @click="$router.push('/events')" variant="ghost">View All</Button>
      </div>
      <div class="divide-y">
        <div
          v-for="event in events"
          :key="event.name"
          class="px-6 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors"
          @click="$router.push(`/events/${event.name}`)"
        >
          <div class="flex items-center gap-4">
            <div class="p-2 rounded-lg bg-gray-50">
              <FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ event.event_name }}</p>
              <p class="text-xs text-gray-500">
                {{ formatDate(event.event_date) }}
                <span v-if="event.event_time"> at {{ event.event_time }}</span>
                <span v-if="event.venue"> · {{ event.venue }}</span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 text-xs text-gray-500">
            <span>{{ event.total_guests || 0 }} guests</span>
            <span>{{ event.total_accepted || 0 }} accepted</span>
            <span :class="statusClass(event.event_status)" class="px-2 py-1 rounded-full text-xs font-medium">
              {{ event.event_status }}
            </span>
          </div>
        </div>
        <div
          v-if="!events.length"
          class="px-6 py-12 text-center text-gray-500"
        >
          <FeatherIcon name="calendar" class="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p class="text-sm">No events yet. Create your first event to get started!</p>
          <Button class="mt-4" @click="$router.push('/events')">Create Event</Button>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div
        class="bg-white rounded-lg border p-5 hover:shadow-md cursor-pointer transition-shadow"
        @click="$router.push('/events')"
      >
        <FeatherIcon name="plus-circle" class="h-8 w-8 text-blue-500 mb-3" />
        <h4 class="text-sm font-medium text-gray-900">Create Event</h4>
        <p class="text-xs text-gray-500 mt-1">Set up a new ceremony or event</p>
      </div>

      <div
        class="bg-white rounded-lg border p-5 hover:shadow-md cursor-pointer transition-shadow"
        @click="goToLatestEvent"
      >
        <FeatherIcon name="user-plus" class="h-8 w-8 text-green-500 mb-3" />
        <h4 class="text-sm font-medium text-gray-900">Manage Guests</h4>
        <p class="text-xs text-gray-500 mt-1">Add or import guests for an event</p>
      </div>

      <div
        class="bg-white rounded-lg border p-5 hover:shadow-md cursor-pointer transition-shadow"
        @click="goToCheckIn"
      >
        <FeatherIcon name="camera" class="h-8 w-8 text-purple-500 mb-3" />
        <h4 class="text-sm font-medium text-gray-900">Check-In</h4>
        <p class="text-xs text-gray-500 mt-1">Scan QR codes for event check-in</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeRequest } from '@/utils/api'

const router = useRouter()
const stats = ref({})
const events = ref([])

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: 'invite.api.reports.dashboard',
    })
    stats.value = data.stats || {}
    events.value = (data.events || []).slice(0, 5)
  } catch (e) {
    console.error('Failed to load dashboard:', e)
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

function goToLatestEvent() {
  if (events.value.length) {
    router.push(`/events/${events.value[0].name}/guests`)
  }
}

function goToCheckIn() {
  if (events.value.length) {
    router.push(`/events/${events.value[0].name}/checkin`)
  }
}
</script>
