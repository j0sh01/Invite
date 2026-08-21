<template>
  <div class="bg-white rounded-lg border mb-6 overflow-x-auto">
    <div class="flex flex-nowrap min-w-0">
      <button
        v-for="tab in eventTabs"
        :key="tab.route"
        @click="navigate(tab.route)"
        class="flex items-center gap-1.5 px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap"
        :class="isActiveTab(tab.route) ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
      >
        <FeatherIcon :name="tab.icon" class="h-4 w-4" />
        {{ tab.label }}
      </button>
    </div>
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
  { label: 'Audit Log', icon: 'file-text', route: '/audit-log' },
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
