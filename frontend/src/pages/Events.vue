<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between gap-4 mb-6">
      <div class="min-w-0 flex-1">
        <h1 class="text-xl sm:text-2xl font-semibold text-gray-900 truncate">Events</h1>
        <p class="text-sm text-gray-500 mt-1 truncate">Manage your ceremonies and events</p>
      </div>
      <Button @click="showCreateModal = true" variant="solid" size="sm" iconLeft="plus" :label="__('New Event')" class="flex-shrink-0" />
    </div>

    <!-- Events Grid -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading events...
    </div>

    <div v-else-if="!events.length" class="text-center py-12 bg-white rounded-lg border">
      <FeatherIcon name="calendar" class="h-16 w-16 mx-auto mb-4 text-gray-300" />
      <h3 class="text-lg font-medium text-gray-900">No events yet</h3>
      <p class="text-sm text-gray-500 mt-1">Create your first event to get started.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="event in events"
        :key="event.name"
        class="bg-white rounded-lg border hover:shadow-lg transition-shadow cursor-pointer"
        @click="$router.push(`/events/${event.name}`)"
      >
        <div v-if="event.image" class="h-40 rounded-t-lg bg-cover bg-center" :style="{ backgroundImage: `url(${event.image})` }" />
        <div v-else class="h-40 rounded-t-lg bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
          <FeatherIcon name="calendar" class="h-12 w-12 text-blue-300" />
        </div>
        <div class="p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
              {{ event.event_type || 'General' }}
            </span>
            <span :class="statusClass(event.event_status)" class="text-xs px-2 py-1 rounded-full">
              {{ event.event_status }}
            </span>
          </div>
          <h3 class="text-base font-semibold text-gray-900 mb-1">{{ event.event_name }}</h3>
          <p class="text-sm text-gray-500 mb-3">
            <FeatherIcon name="map-pin" class="h-3 w-3 inline mr-1" />
            {{ event.venue || 'No venue set' }}
          </p>
          <div class="flex items-center justify-between text-xs text-gray-500 border-t pt-3">
            <span>{{ formatDate(event.event_date) }}</span>
            <div class="flex gap-3">
              <span>{{ event.total_guests || 0 }} guests</span>
              <span>{{ event.total_checked_in || 0 }} checked in</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Event Modal -->
    <Dialog :options="{ title: 'Create New Event' }" v-model="showCreateModal">
      <template #body-content>
        <div class="space-y-4">
          <FormControl label="Event Name" v-model="newEvent.event_name" required />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Event Type" type="select" v-model="newEvent.event_type" :options="eventTypes" />
            <FormControl label="Status" type="select" v-model="newEvent.event_status" :options="eventStatuses" />
          </div>
          <FormControl label="Event Date" type="date" v-model="newEvent.event_date" required />
          <FormControl label="Event Time" type="time" v-model="newEvent.event_time" />
          <FormControl label="Venue" v-model="newEvent.venue" />
          <FormControl label="Location/Address" type="textarea" v-model="newEvent.location_address" />
          <FormControl label="Organizer Name" v-model="newEvent.organizer_name" required />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Organizer Contact" v-model="newEvent.organizer_contact" />
            <FormControl label="Organizer Email" v-model="newEvent.organizer_email" />
          </div>
          <FormControl label="Max Guests" type="number" v-model="newEvent.max_guests" />
          <FormControl label="Description" type="textarea" v-model="newEvent.description" />
        </div>
      </template>
      <template #actions>
        <Button @click="showCreateModal = false" variant="ghost" size="sm">Cancel</Button>
        <Button @click="createEvent" variant="solid" size="sm" :loading="creating">Create Event</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { frappeRequest } from '@/utils/api'

const events = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const creating = ref(false)
const eventTypes = ref([])
const eventStatuses = ref([])

const newEvent = ref({
  event_name: '',
  event_type: '',
  event_status: 'Planning',
  event_date: '',
  event_time: '',
  venue: '',
  location_address: '',
  organizer_name: '',
  organizer_contact: '',
  organizer_email: '',
  max_guests: '',
  description: '',
})

onMounted(async () => {
  await loadEvents()
  await loadOptions()
})

async function loadEvents() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get_list',
    })
    events.value = data.events || []
  } catch (e) {
    console.error('Failed to load events:', e)
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get_options',
    })
    eventTypes.value = (data.event_types || []).map(t => ({ label: t, value: t }))
    eventStatuses.value = (data.event_statuses || []).map(s => ({ label: s, value: s }))
  } catch (e) {
    console.error('Failed to load options:', e)
  }
}

async function createEvent() {
  creating.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.api.event.create',
      params: { data: JSON.stringify(newEvent.value) },
    })
    showCreateModal.value = false
    await loadEvents()
  } catch (e) {
    console.error('Failed to create event:', e)
  } finally {
    creating.value = false
  }
}

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
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
