<template>
  <div>
    <EventWorkspaceHeader :event-id="props.eventId" />

    <!-- Overview modules -->
    <div class="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
      <ModuleTile
        icon="users"
        title="Guests"
        text="Manage and import the guest list"
        tone="violet"
        @click="router.push(`/events/${props.eventId}/guests`)"
      />
      <ModuleTile
        icon="mail"
        title="Invitations"
        text="Send invites and track delivery"
        tone="accent"
        @click="router.push(`/events/${props.eventId}/invitations`)"
      />
      <ModuleTile
        icon="camera"
        title="Check-In"
        text="Scan QR codes at the door"
        tone="green"
        @click="router.push(`/events/${props.eventId}/checkin`)"
      />
    </div>

    <!-- Recent activity -->
    <section class="mt-10">
      <p class="eyebrow mb-4 text-gray-500">Live activity</p>
      <div class="card overflow-hidden">
        <div class="border-b border-[#EFE7D6] px-5 py-4">
          <h3 class="font-display text-lg text-gray-900">Recent check-ins</h3>
        </div>
        <div v-if="recentCheckins.length" class="divide-y divide-[#F3EDE1]">
          <div
            v-for="(ci, i) in recentCheckins"
            :key="ci.name || i"
            class="flex items-center justify-between gap-3 px-5 py-3.5"
          >
            <div class="flex min-w-0 items-center gap-3">
              <div
                class="grid size-8 flex-shrink-0 place-items-center rounded-full"
                :class="ci.is_duplicate ? 'bg-[#FDF6E3] text-[#B45309]' : 'bg-[#F0F7F2] text-[#166534]'"
              >
                <FeatherIcon :name="ci.is_duplicate ? 'refresh-cw' : 'check'" class="size-4" />
              </div>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-gray-800">{{ ci.guest_name }}</p>
                <p class="text-[11px] text-gray-400">
                  {{ ci.is_duplicate ? 'Duplicate scan' : 'Checked in' }}
                </p>
              </div>
            </div>
            <span class="flex-shrink-0 text-xs text-gray-400">
              {{ ci.checked_in_at ? formatDateTime(ci.checked_in_at) : '' }}
            </span>
          </div>
        </div>
        <div v-else class="px-6 py-10 text-center">
          <FeatherIcon name="user-check" class="mx-auto mb-2 size-8 text-[#C4B396]" />
          <p class="text-sm text-gray-500">
            No check-ins yet — open Check-In to scan the first guest.
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import EventWorkspaceHeader from '@/components/EventWorkspaceHeader.vue'
import { formatDateTime } from '@/utils/format'

const props = defineProps({ eventId: String })
const router = useRouter()
const recentCheckins = ref([])

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: 'invite.api.check_in.get_list',
      params: { event: props.eventId, limit: 10 },
    })
    recentCheckins.value = data.checkins || []
  } catch (e) {
    console.error('Failed to load recent check-ins:', e)
  }
})

const ModuleTile = {
  props: { icon: String, title: String, text: String, tone: { type: String, default: 'accent' } },
  emits: ['click'],
  setup(props, { emit }) {
    const chip = {
      accent: 'bg-[#FBF2EC] text-[#B04C21]',
      green: 'bg-[#F0F7F2] text-[#166534]',
      violet: 'bg-[#FAF3FF] text-[#6B21A8]',
    }[props.tone]
    return () =>
      h(
        'button',
        { type: 'button', class: 'card card-hover flex items-start gap-4 p-5 text-left', onClick: () => emit('click') },
        [
          h('span', { class: `grid size-11 flex-shrink-0 place-items-center rounded-xl ${chip}` }, [
            h(FeatherIcon, { name: props.icon, class: 'size-5' }),
          ]),
          h('span', { class: 'min-w-0' }, [
            h('span', { class: 'block text-[15px] font-medium text-gray-900' }, props.title),
            h('span', { class: 'mt-1 block text-xs leading-relaxed text-gray-500' }, props.text),
          ]),
        ],
      )
  },
}
</script>
