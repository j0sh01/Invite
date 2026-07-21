<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Reports</h1>
        <p class="text-sm text-gray-500 mt-1">Event summary and analytics</p>
      </div>
      <div class="flex gap-2">
        <Button @click="activeTab = 'summary'" variant="ghost" :class="activeTab === 'summary' ? 'bg-gray-100' : ''">
          Summary
        </Button>
        <Button @click="activeTab = 'financial'" variant="ghost" :class="activeTab === 'financial' ? 'bg-gray-100' : ''">
          Financial
        </Button>
      </div>
    </div>

    <!-- Sub-navigation Tabs -->
    <EventTabs :eventId="props.eventId" />

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading report data...</div>

    <!-- Summary Tab -->
    <div v-else-if="activeTab === 'summary' && summary">
      <div class="grid grid-cols-3 gap-4 mb-6">
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
        </div>
        <div class="bg-white rounded-lg border p-5">
          <h3 class="text-sm font-medium text-gray-500 mb-1">Check-Ins</h3>
          <p class="text-lg font-semibold text-green-600">{{ summary.checkins?.total || 0 }}</p>
          <p class="text-sm text-gray-500">{{ summary.checkins?.duplicates || 0 }} duplicates</p>
        </div>
      </div>

      <!-- Top Contributors -->
      <div class="bg-white rounded-lg border">
        <div class="px-6 py-4 border-b">
          <h3 class="text-base font-medium text-gray-900">Top Contributors</h3>
        </div>
        <div class="divide-y">
          <div v-for="c in summary.top_contributors" :key="c.guest" class="px-6 py-3 flex justify-between text-sm">
            <span class="text-gray-900">{{ c.guest_name }}</span>
            <span class="font-medium text-green-600">{{ formatCurrency(c.total_paid) }}</span>
          </div>
          <div v-if="!summary.top_contributors?.length" class="px-6 py-8 text-center text-gray-500 text-sm">
            No contributions yet
          </div>
        </div>
      </div>
    </div>

    <!-- Financial Tab -->
    <div v-else-if="activeTab === 'financial' && financialData">
      <div class="grid grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg border p-4 text-center">
          <p class="text-lg font-semibold text-gray-900">{{ formatCurrency(financialData.total_pledged) }}</p>
          <p class="text-xs text-gray-500">Total Pledged</p>
        </div>
        <div class="bg-white rounded-lg border p-4 text-center">
          <p class="text-lg font-semibold text-green-600">{{ formatCurrency(financialData.total_paid) }}</p>
          <p class="text-xs text-gray-500">Total Paid</p>
        </div>
        <div class="bg-white rounded-lg border p-4 text-center">
          <p class="text-lg font-semibold text-amber-600">{{ formatCurrency(financialData.outstanding) }}</p>
          <p class="text-xs text-gray-500">Outstanding</p>
        </div>
        <div class="bg-white rounded-lg border p-4 text-center">
          <p class="text-lg font-semibold text-blue-600">{{ financialData.collection_rate }}%</p>
          <p class="text-xs text-gray-500">Collection Rate</p>
        </div>
      </div>

      <!-- By Type Breakdown -->
      <div class="bg-white rounded-lg border mb-6">
        <div class="px-6 py-4 border-b">
          <h3 class="text-base font-medium text-gray-900">By Contribution Type</h3>
        </div>
        <div class="divide-y">
          <div v-for="t in financialData.by_type" :key="t.contribution_type" class="px-6 py-3 flex justify-between text-sm">
            <span class="text-gray-900">{{ t.contribution_type }}</span>
            <div class="flex gap-6">
              <span>Count: {{ t.count }}</span>
              <span>Pledged: {{ formatCurrency(t.total_pledged) }}</span>
              <span>Paid: {{ formatCurrency(t.total_paid) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- All Contributions -->
      <div class="bg-white rounded-lg border">
        <div class="px-6 py-4 border-b">
          <h3 class="text-base font-medium text-gray-900">All Contributions</h3>
        </div>
        <div class="divide-y">
          <div v-for="c in financialData.contributions" :key="c.guest_name" class="px-6 py-3 flex justify-between text-sm">
            <div>
              <p class="text-gray-900 font-medium">{{ c.guest_name }}</p>
              <p class="text-gray-500">{{ c.contribution_type }} · {{ c.payment_method || '-' }}</p>
            </div>
            <div class="text-right">
              <p class="text-gray-900">{{ formatCurrency(c.paid_amount) }}</p>
              <p v-if="c.outstanding_amount" class="text-xs text-amber-600">Outstanding: {{ formatCurrency(c.outstanding_amount) }}</p>
            </div>
          </div>
          <div v-if="!financialData.contributions?.length" class="px-6 py-8 text-center text-gray-500 text-sm">
            No contributions recorded
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'

const props = defineProps({ eventId: String })
const activeTab = ref('summary')
const loading = ref(true)
const summary = ref(null)
const financialData = ref(null)

onMounted(async () => {
  await loadData()
})

watch(activeTab, () => {
  if (activeTab.value === 'financial' && !financialData.value) {
    loadFinancialReport()
  }
})

async function loadData() {
  loading.value = true
  try {
    [summary.value] = await Promise.all([
      frappeRequest({ url: 'invite.api.reports.event_summary', params: { event: props.eventId } }),
    ])
  } catch (e) {
    console.error('Failed to load reports:', e)
  } finally {
    loading.value = false
  }
}

async function loadFinancialReport() {
  try {
    financialData.value = await frappeRequest({
      url: 'invite.api.reports.financial_report',
      params: { event: props.eventId },
    })
  } catch (e) {
    console.error('Failed to load financial report:', e)
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

function formatCurrency(amount) {
  if (!amount) return 'TZS 0'
  return `TZS ${Number(amount).toLocaleString()}`
}
</script>
