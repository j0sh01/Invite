<template>
  <div class="flex flex-nowrap items-center gap-1 overflow-x-auto rounded-xl border border-[#E7DCC7] bg-paper p-1">
    <button
      v-for="tab in eventTabs"
      :key="tab.route"
      @click="navigate(tab.route)"
      class="flex flex-shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors sm:px-4 sm:text-[13px]"
      :class="
        isActiveTab(tab.route)
          ? 'bg-[#FBF2EC] text-[#8F3B1C] shadow-sm'
          : 'text-gray-500 hover:bg-[#F8F2E6] hover:text-gray-800'
      "
    >
      <FeatherIcon :name="tab.icon" class="size-4" />
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  eventId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const eventTabs = [
  { label: 'Overview', icon: 'eye', route: '' },
  { label: 'Guests', icon: 'users', route: '/guests' },
  { label: 'Invitations', icon: 'mail', route: '/invitations' },
  { label: 'Check-In', icon: 'camera', route: '/checkin' },
  { label: 'Audit Log', icon: 'clipboard', route: '/audit-log' },
  { label: 'Reports', icon: 'bar-chart-2', route: '/reports' },
  { label: 'Settings', icon: 'settings', route: '/settings' },
]

const isOverviewTab = computed(() => {
  return route.path === `/events/${props.eventId}` || route.path === `/events/${props.eventId}/`
})

function isActiveTab(tabRoute) {
  if (!tabRoute) return isOverviewTab.value
  return route.path === `/events/${props.eventId}${tabRoute}`
}

function navigate(tabRoute) {
  router.push(`/events/${props.eventId}${tabRoute}`)
}
</script>
