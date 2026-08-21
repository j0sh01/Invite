<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl sm:text-2xl font-semibold text-gray-900">Reports</h1>
        <p class="text-sm text-gray-500 mt-1">Event summary and analytics</p>
      </div>
      <Button @click="exportGuests" variant="ghost" size="sm" iconLeft="download" :label="__('Export Guests')" />
    </div>

    <!-- Sub-navigation Tabs -->
    <EventTabs :eventId="props.eventId" />

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading report data...</div>

    <div v-else-if="summary">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg border p-5">
          <h3 class="text-sm font-medium text-gray-500 mb-1">Event Info</h3>
          <p class="text-base font-semibold text-gray-900">{{ summary.event?.event_name }}</p>
          <p class="text-sm text-gray-500">{{ summary.event?.event_type }} · {{ formatDate(summary.event?.event_date) }}</p>
          <p class="text-sm text-gray-500">{{ summary.event?.venue }}</p>
        </div>
        <div class="bg-white rounded-lg border p-5">
          <h3 class="text-sm font-medium text-gray-500 mb-1">Guests & RSVPs</h3>
          <div v-for="rsvp in summary.rsvp_by_status" :key="rsvp.rsvp_status" class="flex justify-between text-sm py-1">
            <span>{{ rsvp.rsvp_status }}</span>
            <span class="font-medium">{{ rsvp.count }} ({{ rsvp.attendees || 0 }} attending)</span>
          </div>
          <div v-if="!summary.rsvp_by_status?.length" class="text-sm text-gray-500 py-1">No RSVPs yet</div>
        </div>
        <div class="bg-white rounded-lg border p-5">
          <h3 class="text-sm font-medium text-gray-500 mb-1">Check-Ins</h3>
          <p class="text-lg font-semibold text-green-600">{{ summary.checkins?.total || 0 }}</p>
          <p class="text-sm text-gray-500">{{ summary.checkins?.duplicates || 0 }} duplicates</p>
        </div>
      </div>

      <!-- Guest List Summary -->
      <div class="bg-white rounded-lg border">
        <div class="px-6 py-4 border-b">
          <h3 class="text-base font-medium text-gray-900">Guest Summary by Category</h3>
        </div>
        <div class="divide-y">
          <div v-for="cat in summary.guests_by_category" :key="cat.category" class="px-6 py-3 flex justify-between text-sm">
            <span class="text-gray-900">{{ cat.category || 'Uncategorized' }}</span>
            <span class="font-medium">{{ cat.count }} guests</span>
          </div>
          <div v-if="!summary.guests_by_category?.length" class="px-6 py-8 text-center text-gray-500 text-sm">
            No guests yet
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'

const props = defineProps({ eventId: String })
const loading = ref(true)
const summary = ref(null)

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    summary.value = await frappeRequest({
      url: 'invite.api.reports.event_summary',
      params: { event: props.eventId },
    })
  } catch (e) {
    console.error('Failed to load reports:', e)
  } finally {
    loading.value = false
  }
}

async function exportGuests() {
  try {
    const guests = await frappeRequest({
      url: 'invite.api.reports.guest_list',
      params: { event: props.eventId },
    })
    
    // Convert to CSV
    if (!guests?.length) {
      alert('No guests to export')
      return
    }
    
    const headers = ['Name', 'Email', 'Mobile', 'Category', 'RSVP Status', 'Checked In', 'Number of Attendees']
    const rows = guests.map(g => [
      g.full_name, g.email || '', g.mobile_no || '', g.category || '',
      g.rsvp_status || 'Pending', g.checked_in ? 'Yes' : 'No', g.number_of_attendees || 1
    ])
    
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `guests_${props.eventId}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Failed to export guests:', e)
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
</script>
