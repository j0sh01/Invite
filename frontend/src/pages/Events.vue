<template>
  <div>
    <PageHeader
      eyebrow="Library"
      title="Events"
      subtitle="Plan ceremonies and manage each event's guests, invitations and check-in."
    >
      <template #actions>
        <Button variant="solid" iconLeft="plus" @click="openCreateModal">
          New Event
        </Button>
      </template>
    </PageHeader>

    <!-- Toolbar -->
    <div v-if="events.length" class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
      <div class="relative flex-1 sm:max-w-xs">
        <FeatherIcon
          name="search"
          class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400"
        />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by name or venue…"
          class="w-full rounded-xl border border-[#E0D3BA] bg-paper py-2.5 pl-9 pr-3 text-sm text-gray-800 placeholder:text-gray-400 focus:border-[#B04C21] focus:outline-none focus:ring-[3px] focus:ring-[#8F3B1C]/10"
        />
      </div>
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          v-for="option in filterOptions"
          :key="option.value"
          class="rounded-full border px-3 py-1.5 text-xs font-medium transition-colors"
          :class="
            activeStatus === option.value
              ? 'border-[#B04C21] bg-[#FBF2EC] text-[#8F3B1C]'
              : 'border-[#E0D3BA] bg-paper text-gray-600 hover:border-[#C4B396]'
          "
          @click="activeStatus = option.value"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <!-- States -->
    <EmptyState
      v-if="!loading && !events.length"
      icon="calendar"
      title="No events yet"
      message="Create your first event to start inviting guests and managing check-in."
    >
      <template #action>
        <Button variant="solid" iconLeft="plus" @click="openCreateModal">
          Create Event
        </Button>
      </template>
    </EmptyState>

    <div v-else-if="loading" class="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
      <div v-for="n in 6" :key="n" class="card h-72 animate-pulse bg-[#F3EDE0]" />
    </div>

    <EmptyState
      v-else-if="!filteredEvents.length"
      icon="search"
      title="Nothing matches"
      message="Try a different search term or status filter."
    />

    <div v-else class="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
      <article
        v-for="event in filteredEvents"
        :key="event.name"
        class="card card-hover group cursor-pointer overflow-hidden"
        @click="router.push(`/events/${event.name}`)"
      >
        <!-- Cover -->
        <div
          v-if="event.image"
          class="h-36 bg-cover bg-center"
          :style="{ backgroundImage: `url(${event.image})` }"
        />
        <div
          v-else
          class="relative h-28 bg-gradient-to-br from-[#F7E2D4] via-[#F1E3CC] to-[#E9D5B8]"
        >
          <FeatherIcon
            name="calendar"
            class="absolute right-4 top-4 size-6 text-[#C98F6A]/70"
          />
          <div class="absolute bottom-3 left-4 flex items-center gap-2">
            <span class="font-display text-3xl text-[#8F3B1C]/80">
              {{ dayOf(event.event_date) }}
            </span>
            <span class="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#8F3B1C]/60">
              {{ monthOf(event.event_date) }}
            </span>
          </div>
        </div>

        <div class="p-5">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="eyebrow text-[#A05C38]">{{ event.event_type || 'General' }}</p>
              <h3 class="font-display mt-1.5 truncate text-xl text-gray-900 group-hover:text-[#8F3B1C]">
                {{ event.event_name }}
              </h3>
            </div>
            <StatusBadge :status="event.event_status" />
          </div>

          <p class="mt-3 flex items-center gap-1.5 text-xs text-gray-500">
            <FeatherIcon name="map-pin" class="size-3.5 text-[#B9A887]" />
            <span class="truncate">{{ event.venue || 'Venue not set' }}</span>
          </p>

          <div class="mt-4 flex items-center justify-between border-t border-[#EFE7D6] pt-3.5 text-xs text-gray-500">
            <span class="inline-flex items-center gap-1.5">
              <FeatherIcon name="users" class="size-3.5 text-[#B9A887]" />
              {{ event.total_guests || 0 }} guests
            </span>
            <span class="inline-flex items-center gap-1.5">
              <FeatherIcon name="check-circle" class="size-3.5 text-[#16A34A]" />
              {{ event.total_checked_in || 0 }} checked in
            </span>
          </div>
        </div>
      </article>
    </div>

    <!-- Create Event Modal -->
    <Dialog :options="{ title: 'Create New Event', size: 'xl' }" v-model="showCreateModal">
      <template #body-content>
        <div class="space-y-5">
          <div>
            <p class="eyebrow mb-3 text-gray-500">Basics</p>
            <div class="space-y-4">
              <FormControl label="Event Name" v-model="newEvent.event_name" required placeholder="e.g. John & Mary's Wedding" />
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormControl label="Event Type" type="select" v-model="newEvent.event_type" :options="eventTypes" />
                <FormControl label="Status" type="select" v-model="newEvent.event_status" :options="eventStatuses" />
              </div>
              <FormControl
                label="Invitation Card Template"
                type="select"
                v-model="newEvent.invitation_template"
                :options="templateOptions"
                :disabled="!templateOptions.length"
              />
              <p v-if="!templateOptions.length" class="-mt-2 text-xs text-gray-500">
                No templates yet — add one under
                <RouterLink to="/templates" class="text-[#8F3B1C] underline">Templates</RouterLink>.
              </p>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormControl label="Event Date" type="date" v-model="newEvent.event_date" required />
                <FormControl label="Event Time" type="time" v-model="newEvent.event_time" />
              </div>
              <FormControl label="Venue" v-model="newEvent.venue" placeholder="Where is it happening?" />
              <FormControl label="Location / Address" type="textarea" v-model="newEvent.location_address" />
            </div>
          </div>

          <div>
            <p class="eyebrow mb-3 text-gray-500">Organiser</p>
            <div class="space-y-4">
              <FormControl label="Organizer Name" v-model="newEvent.organizer_name" required />
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormControl label="Organizer Contact" v-model="newEvent.organizer_contact" />
                <FormControl label="Organizer Email" v-model="newEvent.organizer_email" />
              </div>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormControl label="Max Guests" type="number" v-model="newEvent.max_guests" />
                <FormControl label="Description" type="textarea" v-model="newEvent.description" />
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button variant="ghost" @click="showCreateModal = false">Cancel</Button>
        <Button variant="solid" :loading="creating" @click="createEvent">Create Event</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FeatherIcon, Button, Dialog, FormControl } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const events = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const creating = ref(false)
const eventTypes = ref([])
const eventStatuses = ref([])
const templates = ref([])
const searchQuery = ref('')
const activeStatus = ref('All')

const newEvent = ref({
  event_name: '',
  event_type: '',
  invitation_template: '',

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

const templateOptions = computed(() =>
  (templates.value || []).map((t) => ({ label: t.title, value: t.name }))
)

const filterOptions = computed(() => {
  const statuses = [...new Set(events.value.map((e) => e.event_status).filter(Boolean))]
  return [{ label: 'All', value: 'All' }, ...statuses.map((s) => ({ label: s, value: s }))]
})

const filteredEvents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return events.value.filter((event) => {
    const matchesStatus = activeStatus.value === 'All' || event.event_status === activeStatus.value
    const matchesQuery =
      !q ||
      (event.event_name || '').toLowerCase().includes(q) ||
      (event.venue || '').toLowerCase().includes(q) ||
      (event.event_type || '').toLowerCase().includes(q)
    return matchesStatus && matchesQuery
  })
})

onMounted(async () => {
  await Promise.all([loadEvents(), loadOptions()])
  if (route.query.new === '1') {
    openCreateModal()
    router.replace({ query: {} })
  }
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
    const [data, templateData] = await Promise.all([
      frappeRequest({ url: 'invite.api.event.get_options' }),
      frappeRequest({ url: 'invite.api.template.get_options' }).catch(() => ({ templates: [] })),
    ])
    eventTypes.value = (data.event_types || []).map((t) => ({ label: t, value: t }))
    eventStatuses.value = (data.event_statuses || []).map((s) => ({ label: s, value: s }))
    templates.value = templateData?.templates || []
  } catch (e) {
    console.error('Failed to load options:', e)
  }
}

function openCreateModal() {
  showCreateModal.value = true
}

async function createEvent() {
  if (!newEvent.value.event_name || !newEvent.value.event_date) {
    return
  }
  creating.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.api.event.create',
      params: { data: JSON.stringify(newEvent.value) },
    })
    showCreateModal.value = false
    resetForm()
    await loadEvents()
    if (result?.name) {
      router.push(`/events/${result.name}`)
    }
  } catch (e) {
    console.error('Failed to create event:', e)
  } finally {
    creating.value = false
  }
}

function resetForm() {
  Object.assign(newEvent.value, {
    event_name: '',
    event_type: '',
    invitation_template: '',
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
}

function dayOf(date) {
  if (!date) return ''
  const d = new Date(date)
  return isNaN(d.getTime()) ? '' : d.getDate()
}

function monthOf(date) {
  if (!date) return ''
  const d = new Date(date)
  return isNaN(d.getTime())
    ? ''
    : d.toLocaleDateString('en-US', { month: 'short' }).replace('.', '')
}
</script>
