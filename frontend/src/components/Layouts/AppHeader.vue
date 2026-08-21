<template>
  <div class="flex border-b pr-5 min-h-[49px]">
    <!-- Hamburger button for collapsed/overlay sidebar -->
    <div class="flex items-center px-2">
      <button
        @click="$emit('toggle-sidebar')"
        class="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
        :title="isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <FeatherIcon
          :name="isOverlayMode && sidebarExpanded ? 'x' : 'menu'"
          class="h-5 w-5"
        />
      </button>
    </div>

    <div id="app-header" class="flex-1 flex items-center px-2">
      <h2 class="text-lg font-medium text-ink-gray-9">{{ pageTitle }}</h2>
    </div>
    <div class="flex items-center justify-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { useRoute } from 'vue-router'

defineEmits(['toggle-sidebar'])

const route = useRoute()

const isSidebarCollapsed = inject('isSidebarCollapsed', ref(false))
const isOverlayMode = inject('isOverlayMode', ref(false))
const sidebarExpanded = inject('sidebarExpanded', ref(false))

const pageTitle = computed(() => {
  const name = route.name
  const titles = {
    'Dashboard': 'Dashboard',
    'Events': 'Events',
    'EventDetail': 'Event Details',
    'Guests': 'Guests',
    'Invitations': 'Invitations',
    'CheckIn': 'Check-In',
    'Reports': 'Reports',
    'EventSettings': 'Event Settings',
  }
  return titles[name] || 'Invite'
})
</script>
