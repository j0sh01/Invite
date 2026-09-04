<template>
  <div class="max-w-7xl mx-auto">
    <!-- Step 1: Event Selector -->
    <div v-if="!selectedEvent" class="max-w-lg mx-auto py-8 sm:py-16">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-100 mb-4">
          <FeatherIcon name="camera" class="h-8 w-8 text-blue-600" />
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Frontdesk Check-In</h1>
        <p class="text-sm text-gray-500">Select an event to start scanning guests</p>
      </div>

      <div class="bg-white rounded-xl border p-6 shadow-sm">
        <p class="text-sm font-medium text-gray-700 mb-3">Choose Event</p>
        <div v-if="loadingEvents" class="text-center py-6 text-gray-500 text-sm">
          Loading events...
        </div>
        <div v-else-if="!events.length" class="text-center py-6">
          <FeatherIcon name="calendar" class="h-10 w-10 mx-auto mb-2 text-gray-300" />
          <p class="text-sm text-gray-500">No events found</p>
        </div>
        <div v-else class="space-y-3">
          <button
            v-for="event in events"
            :key="event.name"
            @click="selectEvent(event)"
            class="w-full text-left p-4 rounded-lg border-2 transition-all hover:border-blue-400 hover:bg-blue-50 flex items-center justify-between group"
          >
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-gray-900 truncate group-hover:text-blue-700">{{ event.event_name }}</p>
              <p class="text-xs text-gray-500 mt-0.5">
                {{ formatDate(event.event_date) }}
                <span v-if="event.venue"> · {{ event.venue }}</span>
              </p>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0 ml-3">
              <span class="text-xs text-gray-500">{{ event.total_guests || 0 }} guests</span>
              <FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Step 2: Scanning Interface -->
    <div v-else>
      <!-- Event header bar -->
      <div class="bg-white rounded-lg border px-4 sm:px-6 py-3 mb-4 flex items-center justify-between">
        <div class="flex items-center gap-3 min-w-0">
          <button @click="deselectEvent" class="text-gray-400 hover:text-gray-600 flex-shrink-0">
            <FeatherIcon name="arrow-left" class="h-5 w-5" />
          </button>
          <div class="min-w-0">
            <p class="text-sm font-semibold text-gray-900 truncate">{{ selectedEvent.event_name }}</p>
            <p class="text-xs text-gray-500">{{ stats.unique_checkins || 0 }} / {{ stats.total_guests || 0 }} checked in</p>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="relative flex h-2.5 w-2.5" v-if="scannerOn">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
          </span>
          <span class="text-xs font-medium" :class="scannerOn ? 'text-green-600' : 'text-gray-500'">
            {{ scannerOn ? 'Scanning' : 'Paused' }}
          </span>
        </div>
      </div>

      <!-- Stats bar -->
      <div class="grid grid-cols-4 gap-2 sm:gap-3 mb-4">
        <div class="bg-white rounded-lg border p-3 text-center">
          <p class="text-lg sm:text-xl font-bold text-gray-900">{{ stats.total_guests || 0 }}</p>
          <p class="text-[10px] sm:text-xs text-gray-500">Total</p>
        </div>
        <div class="bg-white rounded-lg border p-3 text-center">
          <p class="text-lg sm:text-xl font-bold text-green-600">{{ stats.unique_checkins || 0 }}</p>
          <p class="text-[10px] sm:text-xs text-gray-500">Checked In</p>
        </div>
        <div class="bg-white rounded-lg border p-3 text-center">
          <p class="text-lg sm:text-xl font-bold text-blue-600">{{ stats.rsvp_accepted || 0 }}</p>
          <p class="text-[10px] sm:text-xs text-gray-500">Accepted</p>
        </div>
        <div class="bg-white rounded-lg border p-3 text-center">
          <p class="text-lg sm:text-xl font-bold text-amber-600">{{ stats.checkin_rate || 0 }}%</p>
          <p class="text-[10px] sm:text-xs text-gray-500">Rate</p>
        </div>
      </div>

      <!-- Main scanning area -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Scanner panel (large) -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg border p-4 sm:p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-semibold text-gray-900">QR Scanner</h3>
              <Button
                @click="toggleScanner"
                :variant="scannerOn ? 'solid' : 'ghost'"
                size="sm"
                theme="green"
              >
                <FeatherIcon :name="scannerOn ? 'pause' : 'play'" class="h-3.5 w-3.5 mr-1.5" />
                {{ scannerOn ? 'Pause' : 'Start' }}
              </Button>
            </div>

            <QrScanner ref="qrScannerRef" @detected="onQrDetected" @active-change="onScannerActiveChange" />

            <!-- Manual code entry -->
            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="flex gap-2">
                <Input
                  v-model="qrInput"
                  placeholder="Enter invite code manually..."
                  class="flex-1"
                  @keyup.enter="processQR"
                />
                <Button @click="processQR" size="sm" :loading="processingQR" theme="green">
                  Check In
                </Button>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick search & recent -->
        <div class="space-y-4">
          <!-- Manual search -->
          <div class="bg-white rounded-lg border p-4">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">Quick Search</h3>
            <Input
              v-model="searchQuery"
              placeholder="Search by name, code, phone..."
              class="mb-3"
              @input="onSearchInput"
            />
            <div v-if="searchResults.length" class="space-y-2 max-h-64 overflow-y-auto">
              <div
                v-for="guest in searchResults"
                :key="guest.name"
                class="flex items-center justify-between p-2.5 rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-medium text-gray-900 truncate">{{ guest.full_name }}</p>
                  <p class="text-[10px] text-gray-400 truncate">{{ guest.invite_code }} <span v-if="guest.mobile_no">· {{ guest.mobile_no }}</span></p>
                </div>
                <Button @click="manualCheckIn(guest)" variant="solid" size="xs" theme="green" class="flex-shrink-0 ml-2">
                  Check In
                </Button>
              </div>
            </div>
            <p v-else-if="searchQuery && searchQuery.length >= 2 && !searching" class="text-xs text-gray-500 text-center py-3">
              No guests found
            </p>
          </div>

          <!-- Recent check-ins -->
          <div class="bg-white rounded-lg border p-4">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">Recent</h3>
            <div class="space-y-2 max-h-80 overflow-y-auto">
              <div v-for="ci in recentCheckins" :key="ci.name" class="flex items-center gap-2 text-xs">
                <FeatherIcon
                  :name="ci.is_duplicate ? 'alert-circle' : 'check-circle'"
                  :class="ci.is_duplicate ? 'text-amber-500' : 'text-green-500'"
                  class="h-3.5 w-3.5 flex-shrink-0"
                />
                <div class="min-w-0 flex-1">
                  <p class="text-gray-900 truncate">{{ ci.guest_name }}</p>
                  <p class="text-gray-400">{{ formatTime(ci.checked_in_at) }}</p>
                </div>
              </div>
              <p v-if="!recentCheckins.length" class="text-xs text-gray-500 text-center py-3">No check-ins yet</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Result overlay (full-screen flash) -->
    <Transition name="fade">
      <div
        v-if="showResultOverlay"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        @click="closeResultOverlay"
      >
        <div
          class="mx-4 max-w-sm w-full rounded-2xl p-6 shadow-2xl text-center transform transition-all"
          :class="overlayResult?.success ? 'bg-white' : 'bg-white'"
          @click.stop
        >
          <!-- Success state -->
          <template v-if="overlayResult?.success && !overlayResult?.is_duplicate">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-4">
              <FeatherIcon name="check" class="h-10 w-10 text-green-600" />
            </div>
            <h2 class="text-2xl font-bold text-green-700 mb-1">Welcome!</h2>
            <p class="text-lg text-gray-900 font-semibold mb-1">{{ overlayResult.guest_name }}</p>
            <p class="text-sm text-green-600">Checked in successfully</p>
            <p v-if="overlayResult.attendees && overlayResult.attendees > 1" class="text-xs text-gray-500 mt-2">{{ overlayResult.attendees }} guest(s) in this party</p>
          </template>

          <!-- Duplicate state -->
          <template v-else-if="overlayResult?.success && overlayResult?.is_duplicate">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-amber-100 mb-4">
              <FeatherIcon name="alert-circle" class="h-10 w-10 text-amber-600" />
            </div>
            <h2 class="text-2xl font-bold text-amber-700 mb-1">Already Checked In</h2>
            <p class="text-lg text-gray-900 font-semibold mb-1">{{ overlayResult.guest_name }}</p>
            <p class="text-sm text-amber-600">This guest has already been scanned</p>
            <p class="text-xs text-gray-400 mt-2">No action taken — this is a duplicate scan</p>
          </template>

          <!-- Invalid code / not found -->
          <template v-else-if="overlayResult?.error_type === 'not_found'">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-100 mb-4">
              <FeatherIcon name="search" class="h-10 w-10 text-red-600" />
            </div>
            <h2 class="text-2xl font-bold text-red-700 mb-1">Not Found</h2>
            <p class="text-sm text-gray-600 mb-1">{{ overlayResult.message }}</p>
            <p class="text-xs text-gray-400 mt-2">Please verify the code or try searching manually</p>
          </template>

          <!-- General error -->
          <template v-else-if="overlayResult?.error_type === 'error'">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-100 mb-4">
              <FeatherIcon name="alert-triangle" class="h-10 w-10 text-red-600" />
            </div>
            <h2 class="text-2xl font-bold text-red-700 mb-1">Scan Failed</h2>
            <p class="text-sm text-gray-600">{{ overlayResult.message }}</p>
          </template>

          <!-- Fallback error state -->
          <template v-else-if="!overlayResult?.success">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-100 mb-4">
              <FeatherIcon name="x" class="h-10 w-10 text-red-600" />
            </div>
            <h2 class="text-2xl font-bold text-red-700 mb-1">Check-In Failed</h2>
            <p class="text-sm text-gray-600">{{ overlayResult?.message || 'Invalid or expired code' }}</p>
          </template>

          <p class="text-[10px] text-gray-400 mt-4">Tap anywhere to dismiss</p>
        </div>
      </div>
    </Transition>

    <!-- Result modal (fallback) -->
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
              <p v-if="checkinResult?.is_duplicate" class="text-xs text-amber-600 mt-1">
                ⚠ Duplicate scan — guest was already checked in.
              </p>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showResultModal = false" variant="solid" size="sm">Close</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { frappeRequest } from '@/utils/api'
import QrScanner from '@/components/QrScanner.vue'

// State
const events = ref([])
const loadingEvents = ref(true)
const selectedEvent = ref(null)

const stats = ref({})
const recentCheckins = ref([])

const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)

const qrInput = ref('')
const processingQR = ref(false)
const qrScannerRef = ref(null)
// Real camera state, reported by QrScanner via active-change
const scannerOn = ref(false)
const wasScanningBeforeResult = ref(false)

const showResultModal = ref(false)
const showResultOverlay = ref(false)
const checkinResult = ref(null)
const overlayResult = ref(null)

let searchTimeout = null

onMounted(async () => {
  await loadEvents()
})

async function loadEvents() {
  loadingEvents.value = true
  try {
    const data = await frappeRequest({ url: 'invite.api.event.get_list' })
    events.value = data.events || []
  } catch (e) {
    console.error('Failed to load events:', e)
  } finally {
    loadingEvents.value = false
  }
}

function selectEvent(event) {
  selectedEvent.value = event
  loadStats()
  loadRecentCheckins()
}

function deselectEvent() {
  selectedEvent.value = null
  stats.value = {}
  recentCheckins.value = []
  searchQuery.value = ''
  searchResults.value = []
}

async function loadStats() {
  if (!selectedEvent.value) return
  try {
    stats.value = await frappeRequest({
      url: 'invite.api.check_in.get_stats',
      params: { event: selectedEvent.value.name },
    })
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

async function loadRecentCheckins() {
  if (!selectedEvent.value) return
  try {
    const data = await frappeRequest({
      url: 'invite.api.check_in.get_list',
      params: { event: selectedEvent.value.name, limit: 15 },
    })
    recentCheckins.value = data.checkins || []
  } catch (e) {
    console.error('Failed to load check-ins:', e)
  }
}

function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => searchGuests(), 300)
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
      params: { event: selectedEvent.value.name, query: searchQuery.value },
    })
  } catch (e) {
    console.error('Failed to search guests:', e)
  } finally {
    searching.value = false
  }
}

function toggleScanner() {
  if (scannerOn.value) {
    qrScannerRef.value?.stopCamera()
  } else {
    qrScannerRef.value?.startCamera()
  }
}

function onScannerActiveChange(active) {
  scannerOn.value = active
}

// Pause the camera while a check-in result is being shown so the same card
// can't be re-scanned mid-flow, then automatically resume afterwards.
function beginCheckinFlow() {
  wasScanningBeforeResult.value = scannerOn.value
  qrScannerRef.value?.stopCamera()
}

function closeResultOverlay() {
  showResultOverlay.value = false
  if (wasScanningBeforeResult.value) {
    qrScannerRef.value?.startCamera()
  }
  wasScanningBeforeResult.value = false
}

function onQrDetected(code) {
  qrInput.value = (code || '').trim()
  processQR()
}

async function processQR() {
  qrInput.value = (qrInput.value || '').trim()
  if (!qrInput.value || !selectedEvent.value) return
  beginCheckinFlow()
  processingQR.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.invite.doctype.check_in.check_in.scan_qr',
      params: { code: qrInput.value, event: selectedEvent.value.name },
    })

    // Show overlay for quick visual feedback
    overlayResult.value = {
      success: true,
      guest_name: result.guest_name,
      is_duplicate: result.is_duplicate,
      attendees: result.number_of_attendees || 1,
    }
    showResultOverlay.value = true
    setTimeout(() => { closeResultOverlay() }, 2500)

    qrInput.value = ''
    await Promise.all([loadStats(), loadRecentCheckins()])
  } catch (e) {
    const msg = e.messages?.[0] || e.message || 'Invalid or expired code'
    const errorType = msg.toLowerCase().includes('not found') || msg.toLowerCase().includes('invalid')
      ? 'not_found'
      : 'error'
    overlayResult.value = {
      success: false,
      error_type: errorType,
      message: msg,
    }
    showResultOverlay.value = true
    setTimeout(() => { closeResultOverlay() }, 3000)
  } finally {
    processingQR.value = false
  }
}

async function manualCheckIn(guest) {
  if (!selectedEvent.value) return
  beginCheckinFlow()
  try {
    const result = await frappeRequest({
      url: 'invite.invite.doctype.check_in.check_in.manual_checkin',
      params: { event: selectedEvent.value.name, guest: guest.name },
    })

    overlayResult.value = {
      success: true,
      guest_name: result.guest_name || guest.full_name,
      is_duplicate: result.is_duplicate,
      attendees: result.number_of_attendees || 1,
    }
    showResultOverlay.value = true
    setTimeout(() => { closeResultOverlay() }, 2500)

    searchQuery.value = ''
    searchResults.value = []
    await Promise.all([loadStats(), loadRecentCheckins()])
  } catch (e) {
    const msg = e.messages?.[0] || e.message || 'Check-in failed'
    const errorType = msg.toLowerCase().includes('not found') || msg.toLowerCase().includes('invalid')
      ? 'not_found'
      : 'error'
    overlayResult.value = {
      success: false,
      error_type: errorType,
      message: msg,
    }
    showResultOverlay.value = true
    setTimeout(() => { closeResultOverlay() }, 3000)
  }
}

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

function formatTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
