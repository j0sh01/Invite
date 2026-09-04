<template>
  <div>
    <!-- Back -->
    <button
      class="mb-5 inline-flex items-center gap-1.5 text-xs font-medium text-gray-500 transition-colors hover:text-[#8F3B1C]"
      @click="router.push('/events')"
    >
      <FeatherIcon name="arrow-left" class="size-3.5" />
      All events
    </button>

    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <div class="card h-44 animate-pulse bg-[#F3EDE0]" />
      <div class="card h-12 animate-pulse bg-[#F3EDE0]" />
    </div>

    <!-- Not found -->
    <div v-else-if="!event" class="card px-6 py-12 text-center">
      <FeatherIcon name="alert-circle" class="mx-auto mb-3 size-9 text-[#C4B396]" />
      <p class="text-sm text-gray-600">This event could not be found.</p>
    </div>

    <!-- Event hero -->
    <template v-else>
      <div class="card overflow-hidden">
        <div
          v-if="event.image"
          class="h-36 w-full bg-cover bg-center sm:h-48"
          :style="{ backgroundImage: `url(${event.image})` }"
        />
        <div
          v-else
          class="flex items-center gap-4 bg-gradient-to-r from-[#F7E2D4] via-[#F3E6CF] to-[#EDD9BA] px-5 sm:h-24 sm:px-8"
        >
          <div class="grid size-12 flex-shrink-0 place-items-center rounded-xl bg-white/60">
            <FeatherIcon name="calendar" class="size-6 text-[#B04C21]" />
          </div>
          <div class="min-w-0">
            <p class="eyebrow text-[#9A5A37]">{{ event.event_type || 'Event' }}</p>
            <p class="truncate text-sm text-[#8F3B1C]/70">{{ event.event_status || 'Planning' }}</p>
          </div>
        </div>

        <div class="px-5 py-6 sm:px-8">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="min-w-0">
              <h1 class="font-display text-3xl leading-tight text-gray-900 sm:text-4xl">
                {{ event.event_name }}
              </h1>
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <StatusBadge :status="event.event_status" />
                <span class="text-xs text-gray-400">·</span>
                <p class="text-xs text-gray-500">
                  Organised by
                  <span class="font-medium text-gray-700">{{ event.organizer_name || '—' }}</span>
                </p>
              </div>
            </div>
            <div class="flex flex-shrink-0 gap-2">
              <Button variant="ghost" iconLeft="edit-2" @click="router.push(`/events/${eventId}/settings`)">
                Edit
              </Button>
              <Button variant="solid" iconLeft="users" @click="router.push(`/events/${eventId}/guests`)">
                Guest list
              </Button>
            </div>
          </div>

          <!-- When & where -->
          <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <MetaRow
              icon="calendar"
              label="Date"
              :value="event.event_date ? longDate(event.event_date) : 'Not set'"
            />
            <MetaRow
              icon="clock"
              label="Time"
              :value="event.event_time ? formatTime(event.event_time) : 'All day'"
            />
            <MetaRow
              icon="map-pin"
              label="Venue"
              :value="event.venue || event.location_address || 'Not set'"
            />
          </div>
        </div>

        <!-- Stats strip -->
        <div class="grid grid-cols-3 divide-x divide-[#EFE7D6] border-t border-[#EFE7D6] sm:grid-cols-6">
          <StripStat label="Guests" :value="event.total_guests" />
          <StripStat label="Invited" :value="event.total_invited" />
          <StripStat label="RSVP'd" :value="event.total_rsvped" />
          <StripStat label="Accepted" :value="event.total_accepted" tone="text-[#166534]" />
          <StripStat label="Declined" :value="event.total_declined" tone="text-[#991B1B]" />
          <StripStat label="Checked in" :value="event.total_checked_in" tone="text-[#8F3B1C]" />
        </div>
      </div>

      <!-- Tabs -->
      <div class="mt-6">
        <EventTabs :eventId="eventId" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { FeatherIcon, Button } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { formatDate, formatTime } from '@/utils/format'

const props = defineProps({
  eventId: { type: String, required: true },
})

const router = useRouter()
const event = ref(null)
const loading = ref(true)

async function load() {
  loading.value = true
  event.value = null
  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get',
      params: { event: props.eventId },
    })
    event.value = data.event || null
  } catch (e) {
    console.error('Failed to load event:', e)
    event.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.eventId, load)

function longDate(date) {
  return formatDate(date, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}

const MetaRow = {
  props: { icon: String, label: String, value: String },
  setup(props) {
    return () =>
      h('div', { class: 'flex items-start gap-2.5' }, [
        h(
          'span',
          { class: 'mt-0.5 grid size-8 flex-shrink-0 place-items-center rounded-lg bg-[#F3EDE1] text-[#8A7B61]' },
          [h(FeatherIcon, { name: props.icon, class: 'size-4' })],
        ),
        h('div', { class: 'min-w-0' }, [
          h('p', { class: 'text-[11px] font-semibold uppercase tracking-[0.1em] text-gray-400' }, props.label),
          h('p', { class: 'mt-1 text-sm leading-snug text-gray-800' }, props.value),
        ]),
      ])
  },
}

const StripStat = {
  props: { label: String, value: [String, Number], tone: { type: String, default: 'text-gray-900' } },
  setup(props) {
    return () =>
      h('div', { class: 'px-2 py-4 text-center sm:px-3' }, [
        h('p', { class: `font-display text-xl leading-none sm:text-2xl ${props.tone}` }, String(props.value ?? 0)),
        h('p', { class: 'mt-1.5 text-[10px] font-medium uppercase tracking-[0.1em] text-gray-400' }, props.label),
      ])
  },
}
</script>
