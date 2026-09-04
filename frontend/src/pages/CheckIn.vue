<template>
  <div>
    <EventWorkspaceHeader :event-id="props.eventId" />

    <!-- Content toolbar -->
    <div class="mb-6 mt-8 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="font-display text-xl text-gray-900">Check-In</h2>
        <p class="mt-0.5 text-sm text-gray-500">
          {{ stats.unique_checkins || 0 }} of {{ stats.total_guests || 0 }} guests checked in
        </p>
      </div>
      <div class="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5">
        <span
          class="relative flex h-2 w-2"
        >
          <span
            v-if="scannerOn"
            class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
          ></span>
          <span
            class="relative inline-flex h-2 w-2 rounded-full"
            :class="scannerOn ? 'bg-green-500' : 'bg-gray-300'"
          ></span>
        </span>
        <span class="text-xs font-medium text-gray-600">
          Scanner {{ scannerOn ? 'live' : 'paused' }}
        </span>
      </div>
    </div>

    <!-- Stats -->
    <div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <p class="font-display text-2xl text-gray-900">{{ stats.total_guests || 0 }}</p>
        <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-gray-400">Total Guests</p>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <p class="font-display text-2xl text-green-600">{{ stats.unique_checkins || 0 }}</p>
        <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-gray-400">Checked In</p>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <p class="font-display text-2xl text-blue-600">{{ stats.rsvp_accepted || 0 }}</p>
        <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-gray-400">RSVP Accepted</p>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <p class="font-display text-2xl text-amber-600">{{ stats.checkin_rate || 0 }}%</p>
        <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-gray-400">Check-In Rate</p>
      </div>
    </div>

    <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-3">
      <!-- ==== Left column: scanner console ==== -->
      <div class="space-y-6 lg:col-span-2">
        <!-- Scanner card -->
        <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
            <div class="flex items-center gap-2.5">
              <span class="grid size-8 place-items-center rounded-lg bg-gray-900 text-white">
                <FeatherIcon name="camera" class="size-4" />
              </span>
              <div>
                <h3 class="text-sm font-semibold text-gray-900">QR Scanner</h3>
                <p class="text-xs text-gray-400">Hold a guest's QR code up to the camera</p>
              </div>
            </div>
            <Button
              v-if="scannerOn"
              @click="qrScannerRef?.stopCamera()"
              variant="ghost"
              size="sm"
              iconLeft="pause"
              label="Pause"
            />
          </div>

          <div class="p-5">
            <QrScanner
              ref="qrScannerRef"
              @detected="onQrDetected"
              @active-change="scannerOn = $event"
              @switch-to-manual="showManualEntry = true"
            />

            <!-- Manual code entry (just in case) -->
            <div v-if="showManualEntry" class="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
              <div class="mb-2 flex items-center justify-between">
                <p class="text-xs font-medium text-gray-500">Or paste invite code manually:</p>
                <button @click="showManualEntry = false" class="text-gray-400 hover:text-gray-600">
                  <FeatherIcon name="x" class="h-3.5 w-3.5" />
                </button>
              </div>
              <div class="flex gap-2">
                <Input
                  v-model="qrInput"
                  placeholder="Paste invite code... (URLs also work)"
                  class="flex-1"
                  @keyup.enter="processQR"
                />
                <Button @click="processQR" size="sm" :loading="processingQR">
                  Check In
                </Button>
              </div>
            </div>

            <!-- Last scan strip -->
            <div v-if="lastScan" class="mt-4">
              <div
                class="flex items-center gap-3 rounded-xl border px-4 py-3"
                :class="lastScan.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'"
              >
                <FeatherIcon
                  :name="lastScan.success ? (lastScan.is_duplicate ? 'alert-circle' : 'check-circle') : 'alert-triangle'"
                  :class="lastScan.success ? (lastScan.is_duplicate ? 'text-amber-500' : 'text-green-500') : 'text-red-500'"
                  class="size-5 flex-shrink-0"
                />
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-medium text-gray-900">
                    {{ lastScan.success ? lastScan.guest_name || 'Checked in' : 'Check-in failed' }}
                  </p>
                  <p class="truncate text-xs" :class="lastScan.success ? 'text-gray-500' : 'text-red-600'">
                    {{ lastScan.message }}
                    <span v-if="lastScan.time" class="text-gray-400"> · {{ lastScan.time }}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ==== Right column: manual search + recent ==== -->
      <div class="space-y-6 lg:col-span-1">
        <!-- Manual check-in by search -->
        <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="border-b border-gray-100 px-5 py-4">
            <div class="flex items-center gap-2.5">
              <span class="grid size-8 place-items-center rounded-lg bg-blue-600 text-white">
                <FeatherIcon name="user-check" class="size-4" />
              </span>
              <div>
                <h3 class="text-sm font-semibold text-gray-900">Find a Guest</h3>
                <p class="text-xs text-gray-400">Search by name, invite code or phone</p>
              </div>
            </div>
          </div>
          <div class="p-5">
            <Input
              v-model="searchQuery"
              placeholder="Search guests..."
              class="mb-4"
              @input="searchGuests"
            />

            <div v-if="searchResults.length" class="max-h-80 space-y-2 overflow-y-auto">
              <div
                v-for="guest in searchResults"
                :key="guest.name"
                class="flex items-center justify-between gap-3 rounded-lg border border-gray-200 p-3 transition-colors hover:bg-gray-50"
              >
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-gray-900">{{ guest.full_name }}</p>
                  <p class="truncate text-xs text-gray-400">
                    <span class="font-mono">{{ guest.invite_code }}</span>
                    <span v-if="guest.mobile_no"> · {{ guest.mobile_no }}</span>
                  </p>
                  <p class="text-xs text-gray-400">{{ guest.category }}</p>
                </div>
                <div class="flex flex-shrink-0 items-center gap-2">
                  <span
                    v-if="guest.rsvp_status"
                    :class="rsvpBadge(guest.rsvp_status)"
                    class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  >
                    {{ guest.rsvp_status }}
                  </span>
                  <Button @click="checkInGuest(guest.name, guest.full_name)" variant="solid" size="sm">
                    Check In
                  </Button>
                </div>
              </div>
            </div>

            <div
              v-else-if="searchQuery && !searching"
              class="py-8 text-center text-sm text-gray-400"
            >
              No guests found matching “{{ searchQuery }}”
            </div>
            <div v-else-if="!searchQuery" class="py-4 text-center text-xs text-gray-300">
              Type at least 2 characters to search
            </div>
          </div>
        </div>

        <!-- Recent check-ins -->
        <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
            <div class="flex items-center gap-2.5">
              <span class="grid size-8 place-items-center rounded-lg bg-emerald-600 text-white">
                <FeatherIcon name="activity" class="size-4" />
              </span>
              <h3 class="text-sm font-semibold text-gray-900">Recent Check-Ins</h3>
            </div>
            <span class="text-xs text-gray-400">Last {{ recentCheckins.length }}</span>
          </div>
          <div class="max-h-[26rem] divide-y divide-gray-50 overflow-y-auto">
            <div
              v-for="ci in recentCheckins"
              :key="ci.name"
              class="flex items-center justify-between gap-3 px-5 py-3 text-sm"
            >
              <div class="flex min-w-0 items-center gap-3">
                <FeatherIcon
                  :name="ci.is_duplicate ? 'alert-circle' : 'check-circle'"
                  :class="ci.is_duplicate ? 'text-amber-500' : 'text-emerald-500'"
                  class="size-4 flex-shrink-0"
                />
                <div class="min-w-0">
                  <p class="truncate text-gray-900">{{ ci.guest_name }}</p>
                  <p class="truncate text-xs text-gray-400">
                    {{ ci.check_in_method }} · {{ ci.number_of_attendees || 1 }} guest(s)
                  </p>
                </div>
              </div>
              <div class="flex-shrink-0 text-right">
                <p class="text-xs text-gray-500">{{ ci.checked_in_at ? formatDateTime(ci.checked_in_at) : '' }}</p>
                <p v-if="ci.checked_in_by" class="text-[11px] text-gray-300">by {{ ci.checked_in_by }}</p>
                <p v-if="ci.is_duplicate" class="text-[11px] font-medium text-amber-500">Duplicate scan</p>
              </div>
            </div>
            <div v-if="!recentCheckins.length" class="px-5 py-10 text-center text-sm text-gray-400">
              No check-ins yet — scan the first guest's QR code to get started
            </div>
          </div>
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
// Real camera state, reported by QrScanner via active-change
const scannerOn = ref(false)
const resultWasScanning = ref(false)
const manualWasScanning = ref(false)
const showResultModal = ref(false)
const showManualEntry = ref(false)
const checkinResult = ref(null)
const recentCheckins = ref([])
const lastScan = ref(null)

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

// Pause the camera while manual entry is shown; resume when it is closed again
watch(showManualEntry, (val) => {
  if (val) {
    manualWasScanning.value = scannerOn.value
    qrScannerRef.value?.pauseCamera()
  } else {
    if (manualWasScanning.value) {
      qrScannerRef.value?.startCamera()
    }
    manualWasScanning.value = false
  }
})

// Pause the camera while the result modal is up so the same card can't be
// re-scanned mid-flow; resume automatically when the modal is closed.
watch(showResultModal, (val) => {
  if (val) {
    qrScannerRef.value?.pauseCamera()
  } else {
    if (resultWasScanning.value) {
      qrScannerRef.value?.startCamera()
    }
    resultWasScanning.value = false
    qrScannerRef.value?.clearStatus()
  }
})

function beginCheckinFlow() {
  resultWasScanning.value = scannerOn.value
  qrScannerRef.value?.pauseCamera()
}

function onQrDetected(code) {
  qrInput.value = (code || '').trim()
  showManualEntry.value = false
  processQR()
}

async function processQR() {
  qrInput.value = (qrInput.value || '').trim()
  if (!qrInput.value) return
  beginCheckinFlow()
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
    setLastScan(checkinResult.value)
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
    setLastScan(checkinResult.value)
    showResultModal.value = true
  } finally {
    processingQR.value = false
  }
}

function setLastScan(result) {
  lastScan.value = {
    success: !!result.success,
    guest_name: result.guest_name || null,
    is_duplicate: !!result.is_duplicate,
    message: result.success
      ? result.is_duplicate
        ? 'Already checked in — duplicate scan'
        : 'Checked in successfully'
      : result.message || 'Invalid code',
    time: new Date().toLocaleTimeString(),
  }
}

async function checkInGuest(guestId, guestName) {
  beginCheckinFlow()
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
      setLastScan(checkinResult.value)
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
    setLastScan(checkinResult.value)
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
