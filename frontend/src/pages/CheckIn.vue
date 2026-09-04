<template>
  <div>
    <EventWorkspaceHeader :event-id="props.eventId" />

    <!-- Content toolbar -->
    <div class="mb-5 mt-8 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="font-display text-xl text-gray-900">Check-In</h2>
        <p class="mt-0.5 text-sm text-gray-500">{{ stats.unique_checkins || 0 }} / {{ stats.total_guests || 0 }} guests checked in</p>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-gray-900">{{ stats.total_guests || 0 }}</p>
        <p class="text-xs text-gray-500">Total Guests</p>
      </div>
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-green-600">{{ stats.unique_checkins || 0 }}</p>
        <p class="text-xs text-gray-500">Checked In</p>
      </div>
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-blue-600">{{ stats.rsvp_accepted || 0 }}</p>
        <p class="text-xs text-gray-500">RSVP Accepted</p>
      </div>
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-amber-600">{{ stats.checkin_rate || 0 }}%</p>
        <p class="text-xs text-gray-500">Check-In Rate</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- QR Scanner Area -->
      <div class="bg-white rounded-lg border p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-medium text-gray-900">Scan QR Code</h3>
          <span class="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">Live</span>
        </div>
        <QrScanner ref="qrScannerRef" @detected="onQrDetected" @switch-to-manual="showManualEntry = true" />

        <div v-if="showManualEntry" class="mt-4 pt-4 border-t border-gray-200">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500">Or paste invite code manually:</p>
            <button @click="showManualEntry = false" class="text-gray-400 hover:text-gray-600">
              <FeatherIcon name="x" class="h-3.5 w-3.5" />
            </button>
          </div>
          <div class="flex gap-2">
            <Input
              v-model="qrInput"
              placeholder="Paste invite code..."
              class="flex-1"
              @keyup.enter="processQR"
            />
            <Button @click="processQR" size="sm" :loading="processingQR">
              Check In
            </Button>
          </div>
        </div>
      </div>

      <!-- Manual Check-In -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-base font-medium text-gray-900 mb-4">Manual Check-In</h3>
        <Input
          v-model="searchQuery"
          placeholder="Search by name, invite code, or phone..."
          class="mb-4"
          @input="searchGuests"
        />

        <div v-if="searchResults.length" class="space-y-2 max-h-80 overflow-y-auto">
          <div
            v-for="guest in searchResults"
            :key="guest.name"
            class="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50"
          >
            <div>
              <p class="text-sm font-medium text-gray-900">{{ guest.full_name }}</p>
              <p class="text-xs text-gray-500">
                {{ guest.invite_code }}
                <span v-if="guest.mobile_no"> · {{ guest.mobile_no }}</span>
              </p>
              <p class="text-xs text-gray-400">{{ guest.category }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="guest.rsvp_status" :class="rsvpBadge(guest.rsvp_status)" class="text-xs px-2 py-1 rounded-full">
                {{ guest.rsvp_status }}
              </span>
              <Button @click="checkInGuest(guest.name, guest.full_name)" variant="solid" size="sm">
                Check In
              </Button>
            </div>
          </div>
        </div>

        <div v-else-if="searchQuery && !searching" class="text-center py-8 text-gray-500 text-sm">
          No guests found matching "{{ searchQuery }}"
        </div>
      </div>
    </div>

    <!-- Check-In Result Modal -->
    <Dialog :options="{ title: 'Check-In Result' }" v-model="showResultModal">
      <template #body-content>
        <div class="py-2 space-y-3">
          <div class="flex items-center gap-3 p-4 rounded-lg" :class="checkinResult?.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
            <FeatherIcon :name="checkinResult?.success ? 'check-circle' : 'alert-triangle'" 
              :class="checkinResult?.success ? 'text-green-500' : 'text-red-500'" class="h-10 w-10 flex-shrink-0" />
            <div>
              <p class="text-sm font-medium" :class="checkinResult?.success ? 'text-green-800' : 'text-red-800'">
                {{ checkinResult?.success ? 'Checked In Successfully' : 'Check-In Failed' }}
              </p>
              <p class="text-sm" :class="checkinResult?.success ? 'text-green-700' : 'text-red-700'">
                {{ checkinResult?.message }}
              </p>
              <p v-if="checkinResult?.guest_name" class="text-xs text-gray-500 mt-1">
                Guest: {{ checkinResult?.guest_name }}
              </p>
              <p v-if="checkinResult?.scans_allowed && checkinResult.scans_allowed > 1" class="text-xs font-medium text-blue-600 mt-1">
                Scan {{ checkinResult.scans_used }} of {{ checkinResult.scans_allowed }} — card covers {{ checkinResult.scans_allowed }} people
              </p>
              <p v-if="checkinResult?.is_duplicate" class="text-xs text-amber-600 mt-1">
                ⚠ Duplicate scan — this card's {{ checkinResult.scans_allowed || 1 }} allowed scan(s) have already been used.
              </p>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showResultModal = false" variant="solid" size="sm">Close</Button>
      </template>
    </Dialog>

    <!-- Recent Check-Ins -->
    <div class="bg-white rounded-lg border mt-6">
      <div class="px-6 py-4 border-b">
        <h3 class="text-base font-medium text-gray-900">Recent Check-Ins</h3>
      </div>
      <div class="divide-y">
        <div v-for="ci in recentCheckins" :key="ci.name" class="px-4 sm:px-6 py-3 flex items-center justify-between text-sm">
          <div class="flex items-center gap-3">
            <FeatherIcon :name="ci.is_duplicate ? 'alert-circle' : 'check-circle'"
              :class="ci.is_duplicate ? 'text-amber-500' : 'text-green-500'" class="h-5 w-5" />
            <div>
              <p class="text-gray-900">{{ ci.guest_name }}</p>
              <p class="text-xs text-gray-400">{{ ci.check_in_method }} · {{ ci.number_of_attendees || 1 }} guest(s)</p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-gray-500">{{ ci.checked_in_at ? formatDateTime(ci.checked_in_at) : '' }}</p>
            <p v-if="ci.checked_in_by" class="text-xs text-gray-400">by {{ ci.checked_in_by }}</p>
            <p v-if="ci.is_duplicate" class="text-xs text-amber-500">Duplicate scan</p>
          </div>
        </div>
        <div v-if="!recentCheckins.length" class="px-6 py-8 text-center text-gray-500 text-sm">
          No check-ins yet
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { frappeRequest } from '@/utils/api'
import EventWorkspaceHeader from '@/components/EventWorkspaceHeader.vue'
import QrScanner from '@/components/QrScanner.vue'

const props = defineProps({ eventId: String })

const stats = ref({})
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const qrInput = ref('')
const processingQR = ref(false)
const qrScannerRef = ref(null)
const showResultModal = ref(false)
const showManualEntry = ref(false)
const checkinResult = ref(null)
const recentCheckins = ref([])

onMounted(async () => {
  await Promise.all([loadStats(), loadRecentCheckins()])
})

async function loadStats() {
  try {
    stats.value = await frappeRequest({
      url: 'invite.api.check_in.get_stats',
      params: { event: props.eventId },
    })
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

async function loadRecentCheckins() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.check_in.get_list',
      params: { event: props.eventId, limit: 20 },
    })
    recentCheckins.value = data.checkins || []
  } catch (e) {
    console.error('Failed to load check-ins:', e)
  }
}

async function searchGuests() {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    searchResults.value = await frappeRequest({
      url: 'invite.api.check_in.search_guests',
      params: { event: props.eventId, query: searchQuery.value },
    })
  } catch (e) {
    console.error('Failed to search guests:', e)
  } finally {
    searching.value = false
  }
}

// Pause the camera when manual entry is shown
watch(showManualEntry, (val) => {
  if (val && qrScannerRef.value?.pauseCamera) {
    qrScannerRef.value.pauseCamera()
  }
})

// Clear scanner status when result modal is closed
watch(showResultModal, (val) => {
  if (!val && qrScannerRef.value?.clearStatus) {
    qrScannerRef.value.clearStatus()
  }
})

function onQrDetected(code) {
  qrInput.value = code
  showManualEntry.value = false
  processQR()
}

async function processQR() {
  if (!qrInput.value) return
  processingQR.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.invite.doctype.check_in.check_in.scan_qr',
      params: { code: qrInput.value, event: props.eventId },
    })
    checkinResult.value = {
      success: true,
      message: result.is_duplicate ? 'Guest was already checked in.' : 'Guest has been checked in.',
      guest_name: result.guest_name,
      is_duplicate: result.is_duplicate,
      scans_used: result.scans_used,
      scans_allowed: result.scans_allowed,
    }
    showResultModal.value = true
    qrInput.value = ''
    await Promise.all([loadStats(), loadRecentCheckins()])
  } catch (e) {
    checkinResult.value = {
      success: false,
      message: e.messages?.[0] || e.message || 'Check-in failed',
      guest_name: null,
      is_duplicate: false,
    }
    showResultModal.value = true
  } finally {
    processingQR.value = false
  }
}

async function checkInGuest(guestId, guestName) {
  try {
    const result = await frappeRequest({
      url: 'invite.invite.doctype.check_in.check_in.manual_checkin',
      params: { event: props.eventId, guest: guestId },
    })
    if (result.success) {
      checkinResult.value = {
        success: true,
        message: result.is_duplicate ? 'Guest was already checked in.' : 'Guest has been checked in.',
        guest_name: result.guest_name || guestName,
        is_duplicate: result.is_duplicate,
        scans_used: result.scans_used,
        scans_allowed: result.scans_allowed,
      }
      showResultModal.value = true
      searchQuery.value = ''
      searchResults.value = []
      await Promise.all([loadStats(), loadRecentCheckins()])
    }
  } catch (e) {
    checkinResult.value = {
      success: false,
      message: e.messages?.[0] || e.message || 'Check-in failed',
      guest_name: guestName,
      is_duplicate: false,
    }
    showResultModal.value = true
  }
}

function formatDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString()
}

function rsvpBadge(status) {
  const classes = {
    'Accepted': 'bg-green-50 text-green-700',
    'Declined': 'bg-red-50 text-red-700',
    'Pending': 'bg-gray-50 text-gray-600',
    'Maybe': 'bg-amber-50 text-amber-700',
  }
  return classes[status] || 'bg-gray-50 text-gray-600'
}
</script>
