<template>
  <div>
    <PageHeader
      eyebrow="Overview"
      title="Dashboard"
      subtitle="A quick look at your ceremonies — upcoming events, guest numbers and check-in progress."
    >
      <template #actions>
        <Button variant="solid" iconLeft="plus" @click="router.push('/events?new=1')">
          New Event
        </Button>
      </template>
    </PageHeader>

    <!-- Stats -->
    <div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
      <StatCard label="Total events" :value="stats.total_events || 0" icon="calendar" tone="accent" />
      <StatCard label="Upcoming" :value="stats.upcoming || 0" icon="clock" tone="amber" />
      <StatCard label="Guests" :value="stats.total_guests || 0" icon="users" tone="violet" />
      <StatCard label="Checked in" :value="stats.total_checked_in || 0" icon="check-circle" tone="green" />
    </div>

    <!-- Events -->
    <section class="mt-10">
      <div class="mb-4 flex items-end justify-between gap-3">
        <div>
          <p class="eyebrow text-gray-500">Your events</p>
          <h2 class="font-display mt-1 text-2xl text-gray-900">Upcoming &amp; recent</h2>
        </div>
        <Button variant="ghost" @click="router.push('/events')">View all events</Button>
      </div>

      <EmptyState
        v-if="!events.length"
        icon="calendar"
        title="No events yet"
        message="Create your first event to begin adding guests, sending invitations and checking people in."
      >
        <template #action>
          <Button variant="solid" iconLeft="plus" @click="router.push('/events?new=1')">
            Create your first event
          </Button>
        </template>
      </EmptyState>

      <div v-else class="space-y-3">
        <div
          v-for="event in events"
          :key="event.name"
          class="card card-hover group flex cursor-pointer items-center gap-4 p-4 sm:p-5"
          @click="router.push(`/events/${event.name}`)"
        >
          <!-- Date block -->
          <div
            class="hidden h-[58px] w-[58px] flex-shrink-0 flex-col items-center justify-center rounded-xl border border-[#E7D9C0] bg-[#FAF4E7] sm:flex"
          >
            <span class="font-display text-xl leading-none text-gray-900">
              {{ dayOf(event.event_date) }}
            </span>
            <span class="mt-1 text-[10px] uppercase tracking-[0.12em] text-gray-500">
              {{ monthOf(event.event_date) }}
            </span>
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-x-2.5 gap-y-1">
              <h3 class="font-display truncate text-lg text-gray-900">
                {{ event.event_name }}
              </h3>
              <StatusBadge :status="event.event_status" />
            </div>
            <p class="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
              <span class="inline-flex items-center gap-1.5">
                <FeatherIcon name="tag" class="size-3.5 text-[#B9A887]" />
                {{ event.event_type || 'General' }}
              </span>
              <span class="inline-flex items-center gap-1.5">
                <FeatherIcon name="map-pin" class="size-3.5 text-[#B9A887]" />
                {{ event.venue || 'Venue not set' }}
              </span>
            </p>
          </div>

          <div class="hidden flex-shrink-0 items-center gap-6 lg:flex">
            <div class="text-center">
              <p class="font-display text-lg leading-none text-gray-900">{{ event.total_guests || 0 }}</p>
              <p class="mt-1 text-[11px] uppercase tracking-[0.1em] text-gray-400">guests</p>
            </div>
            <div class="text-center">
              <p class="font-display text-lg leading-none text-gray-900">{{ event.total_accepted || 0 }}</p>
              <p class="mt-1 text-[11px] uppercase tracking-[0.1em] text-gray-400">accepted</p>
            </div>
            <div class="text-center">
              <p class="font-display text-lg leading-none text-gray-900">{{ event.total_checked_in || 0 }}</p>
              <p class="mt-1 text-[11px] uppercase tracking-[0.1em] text-gray-400">checked in</p>
            </div>
          </div>

          <FeatherIcon
            name="chevron-right"
            class="size-5 flex-shrink-0 text-[#C4B396] transition-transform group-hover:translate-x-0.5 group-hover:text-[#B04C21]"
          />
        </div>
      </div>
    </section>

    <!-- Quick actions -->
    <section class="mt-10">
      <p class="eyebrow mb-4 text-gray-500">Shortcuts</p>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <QuickAction
          icon="plus-circle"
          title="Create an event"
          text="Plan a new ceremony or gathering"
          @click="router.push('/events?new=1')"
        />
        <QuickAction
          icon="users"
          title="Manage guests"
          text="Add, import or edit the guest list"
          tone="violet"
          :disabled="!events.length"
          disabled-text="Create an event first"
          @click="router.push(`/events/${events[0].name}/guests`)"
        />
        <QuickAction
          icon="camera"
          title="Run the frontdesk"
          text="Scan QR codes at the door"
          tone="green"
          @click="router.push('/frontdesk')"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { FeatherIcon, Button } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import QuickAction from '@/components/ui/QuickAction.vue'

const router = useRouter()
const stats = ref({})
const events = ref([])

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: 'invite.api.reports.dashboard',
    })
    stats.value = data.stats || {}
    events.value = data.events || []
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  }
})

function dayOf(date) {
  if (!date) return '–'
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
