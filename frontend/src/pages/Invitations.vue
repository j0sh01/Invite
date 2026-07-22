<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Invitations</h1>
        <p class="text-sm text-gray-500 mt-1">{{ totalInvitations }} invitations · {{ sentCount }} sent</p>
      </div>
      <div class="flex gap-2">
        <Button @click="generateBulkInvitations" variant="ghost" size="sm" :loading="generating" iconLeft="zap" :label="__('Generate All')" />
        <Button @click="sendBulk" variant="solid" size="sm" iconLeft="send" :label="__('Send All')" />
      </div>
    </div>

    <!-- Sub-navigation Tabs -->
    <EventTabs :eventId="props.eventId" />

    <!-- Bulk Send Modal -->
    <Dialog :options="{ title: 'Send Invitations' }" v-model="showSendModal">
      <template #body-content>
        <div class="space-y-4">
          <p class="text-sm text-gray-600">
            Send pending invitations for this event. Select the delivery method:
          </p>
          <div class="grid grid-cols-3 gap-3">
            <button
              v-for="medium in deliveryMediums"
              :key="medium.value"
              @click="selectedMedium = medium.value"
              class="flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors"
              :class="selectedMedium === medium.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <FeatherIcon :name="medium.icon" class="h-8 w-8" :class="selectedMedium === medium.value ? 'text-blue-600' : 'text-gray-400'" />
              <span class="text-sm font-medium" :class="selectedMedium === medium.value ? 'text-blue-700' : 'text-gray-600'">{{ medium.label }}</span>
            </button>
          </div>
          <div class="bg-gray-50 rounded-lg p-3 text-sm text-gray-500">
            <p><strong>{{ pendingInvitations.length }}</strong> invitations ready to send</p>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showSendModal = false; sendResult = null" variant="ghost" size="sm">Cancel</Button>
        <Button @click="sendWithMedium" variant="solid" size="sm" :loading="sending" :disabled="!selectedMedium">
          Send via {{ selectedMedium || '...' }}
        </Button>
      </template>
    </Dialog>

    <!-- Send Results Modal -->
    <Dialog :options="{ title: 'Send Results' }" v-model="showSendResultModal">
      <template #body-content>
        <div class="py-2 space-y-3">
          <div class="flex items-center gap-3 p-3 rounded-lg" :class="sendResult?.error ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'">
            <FeatherIcon :name="sendResult?.error ? 'alert-triangle' : 'check-circle'" 
              :class="sendResult?.error ? 'text-red-500' : 'text-green-500'" class="h-8 w-8 flex-shrink-0" />
            <div>
              <p class="text-sm font-medium" :class="sendResult?.error ? 'text-red-800' : 'text-green-800'">
                {{ sendResult?.error ? 'Send Failed' : 'Sent Successfully' }}
              </p>
              <p class="text-xs" :class="sendResult?.error ? 'text-red-600' : 'text-green-600'">
                {{ sendResult?.message }}
              </p>
            </div>
          </div>
          <div v-if="sendResult?.sent?.length" class="bg-blue-50 rounded-lg p-3 text-sm">
            <p class="font-medium text-blue-800 mb-1">Sent ({{ sendResult.sent.length }})</p>
            <p class="text-xs text-blue-600 space-y-0.5 max-h-24 overflow-y-auto">
              <span v-for="s in sendResult.sent" :key="s" class="block">{{ s }}</span>
            </p>
          </div>
          <div v-if="sendResult?.failed?.length" class="bg-red-50 rounded-lg p-3 text-sm">
            <p class="font-medium text-red-800 mb-1">Failed ({{ sendResult.failed.length }})</p>
            <p class="text-xs text-red-600 space-y-0.5 max-h-24 overflow-y-auto">
              <span v-for="f in sendResult.failed" :key="f" class="block">{{ f }}</span>
            </p>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showSendResultModal = false; sendResult = null" variant="solid" size="sm">Close</Button>
      </template>
    </Dialog>

    <!-- Single Send Modal -->
    <Dialog :options="{ title: 'Send Invitation' }" v-model="showSingleSendModal">
      <template #body-content>
        <div class="space-y-4">
          <div v-if="sendingInvitation" class="bg-gray-50 rounded-lg p-3 text-sm">
            <p class="text-gray-700">Sending to: <strong>{{ sendingInvitation?.guest_name }}</strong></p>
            <p class="text-xs text-gray-400 mt-1">Invite code: {{ sendingInvitation?.invite_code }}</p>
          </div>
          <p class="text-sm text-gray-600">Select the delivery method:</p>
          <div class="grid grid-cols-3 gap-3">
            <button
              v-for="medium in deliveryMediums"
              :key="medium.value"
              @click="singleSendMedium = medium.value"
              class="flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors"
              :class="singleSendMedium === medium.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <FeatherIcon :name="medium.icon" class="h-8 w-8" :class="singleSendMedium === medium.value ? 'text-blue-600' : 'text-gray-400'" />
              <span class="text-sm font-medium" :class="singleSendMedium === medium.value ? 'text-blue-700' : 'text-gray-600'">{{ medium.label }}</span>
            </button>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showSingleSendModal = false; sendingInvitation = null" variant="ghost" size="sm">Cancel</Button>
        <Button @click="confirmSingleSend" variant="solid" size="sm" :loading="sending">
          Send via {{ singleSendMedium || '...' }}
        </Button>
      </template>
    </Dialog>

    <!-- Statistics -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-gray-900">{{ stats.total || 0 }}</p>
        <p class="text-xs text-gray-500">Total</p>
      </div>
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-blue-600">{{ stats.sent || 0 }}</p>
        <p class="text-xs text-gray-500">Sent</p>
      </div>
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-green-600">{{ stats.delivered || 0 }}</p>
        <p class="text-xs text-gray-500">Delivered</p>
      </div>
      <div class="bg-white rounded-lg border p-4 text-center">
        <p class="text-lg font-semibold text-red-600">{{ stats.failed || 0 }}</p>
        <p class="text-xs text-gray-500">Failed</p>
      </div>
    </div>

    <!-- Invitations List -->
    <div class="bg-white rounded-lg border overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Guest</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invite Code</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delivery</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">RSVP</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="inv in invitations" :key="inv.name" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm text-gray-900">{{ inv.guest_name }}</td>
            <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ inv.invite_code }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ inv.invitation_type }}</td>
            <td class="px-4 py-3">
              <span :class="statusBadge(inv.status)" class="text-xs px-2 py-1 rounded-full">{{ inv.status }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="text-sm">
                <span :class="deliveryBadge(inv.delivery_status)">{{ inv.delivery_status || 'Pending' }}</span>
                <p v-if="inv.sent_at" class="text-xs text-gray-400 mt-0.5">{{ formatDateTime(inv.sent_at) }}</p>
              </div>
            </td>
            <td class="px-4 py-3">
              <span :class="rsvpBadge(inv.rsvp_status)" class="text-xs px-2 py-1 rounded-full">
                {{ inv.rsvp_status || 'Pending' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex justify-end gap-1">
                <Button v-if="inv.qr_code_image" @click="downloadQR(inv)" variant="ghost" class="text-xs">QR</Button>
                <Button @click="downloadCard(inv)" variant="ghost" class="text-xs" :loading="inv._downloading">Card</Button>
                <Button @click="openSingleSend(inv)" variant="ghost" class="text-xs">Send</Button>
              </div>
            </td>
          </tr>
          <tr v-if="!invitations.length">
            <td colspan="7" class="px-4 py-12 text-center text-gray-500 text-sm">
              No invitations yet. Generate invitations from the Guests page.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'
import { useNotifications } from '@/composables/notifications'

const props = defineProps({ eventId: String })

const invitations = ref([])
const totalInvitations = ref(0)
const generating = ref(false)
const sending = ref(false)
const showSendModal = ref(false)
const showSendResultModal = ref(false)
const showSingleSendModal = ref(false)
const selectedMedium = ref('WhatsApp')
const singleSendMedium = ref('WhatsApp')
const sendingInvitation = ref(null)
const sendResult = ref(null)

const { showError } = useNotifications()

const deliveryMediums = [
  { label: 'WhatsApp', value: 'WhatsApp', icon: 'message-circle' },
  { label: 'SMS', value: 'SMS', icon: 'message-square' },
  { label: 'Email', value: 'Email', icon: 'mail' },
]

const stats = computed(() => {
  const list = invitations.value
  return {
    total: list.length,
    sent: list.filter(i => i.status === 'Sent').length,
    delivered: list.filter(i => i.delivery_status === 'Delivered').length,
    failed: list.filter(i => i.delivery_status === 'Failed' || i.status === 'Failed').length,
  }
})

const sentCount = computed(() => stats.value.sent)

const pendingInvitations = computed(() => {
  return invitations.value.filter(i => i.status === 'Ready' || i.status === 'Draft')
})

onMounted(async () => {
  await loadInvitations()
})

async function loadInvitations() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.invitation.get_list',
      params: { event: props.eventId },
    })
    invitations.value = data.invitations || []
    totalInvitations.value = data.total || 0
  } catch (e) {
    console.error('Failed to load invitations:', e)
  }
}

async function generateBulkInvitations() {
  generating.value = true
  try {
    const { guests } = await frappeRequest({
      url: 'invite.api.guest.get_list',
      params: { event: props.eventId },
    })
    const guestIds = (guests || []).map(g => g.name)
    if (!guestIds.length) {
      sendResult.value = { error: true, message: 'No guests found to invite.', sent: [], failed: [] }
      showSendResultModal.value = true
      return
    }
    await frappeRequest({
      url: 'invite.api.invitation.create_invitations',
      params: { 
        event: props.eventId,
        guest_ids: JSON.stringify(guestIds),
        invitation_type: 'Digital',
        delivery_method: selectedMedium.value,
      },
    })
    sendResult.value = { error: false, message: 'Invitations generated successfully.', sent: [], failed: [] }
    showSendResultModal.value = true
    await loadInvitations()
  } catch (e) {
    console.error('Failed to generate invitations:', e)
    sendResult.value = { error: true, message: e.message || 'Failed to generate invitations', sent: [], failed: [] }
    showSendResultModal.value = true
  } finally {
    generating.value = false
  }
}

async function sendWithMedium() {
  sending.value = true
  try {
    const result = await frappeRequest({
      url: 'invite.api.invitation.send',
      params: { 
        event: props.eventId, 
        invitation_type: selectedMedium.value,
      },
    })
    showSendModal.value = false
    sendResult.value = {
      error: false,
      message: `Sent ${result.sent?.length || 0} invitations, ${result.failed?.length || 0} failed.`,
      sent: result.sent || [],
      failed: result.failed || [],
    }
    showSendResultModal.value = true
    await loadInvitations()
  } catch (e) {
    console.error('Failed to send invitations:', e)
    sendResult.value = { error: true, message: e.message || 'Failed to send', sent: [], failed: [] }
    showSendResultModal.value = true
  } finally {
    sending.value = false
  }
}

async function sendBulk() {
  selectedMedium.value = 'WhatsApp'
  showSendModal.value = true
}

async function openSingleSend(inv) {
  sendingInvitation.value = inv
  singleSendMedium.value = inv.delivery_method || 'WhatsApp'
  showSingleSendModal.value = true
}

async function confirmSingleSend() {
  sending.value = true
  try {
    await frappeRequest({
      url: 'invite.invite.doctype.invitation.invitation.send_invitations',
      params: { 
        event: props.eventId, 
        invitation_type: singleSendMedium.value,
      },
    })
    showSingleSendModal.value = false
    sendResult.value = {
      error: false,
      message: `Invitation sent via ${singleSendMedium.value}.`,
      sent: [sendingInvitation.value?.guest_name || 'Invitation'],
      failed: [],
    }
    showSendResultModal.value = true
    sendingInvitation.value = null
    await loadInvitations()
  } catch (e) {
    console.error('Failed to send invitation:', e)
    sendResult.value = { error: true, message: e.message || 'Failed to send invitation', sent: [], failed: [] }
    showSendResultModal.value = true
  } finally {
    sending.value = false
  }
}

async function downloadCard(inv) {
  inv._downloading = true
  try {
    const result = await frappeRequest({
      url: 'invite.api.card.generate_invitation_card',
      params: { invitation: inv.name },
    })
    if (result.card_url) {
      window.open(result.card_url, '_blank')
    }
  } catch (e) {
    console.error('Failed to generate card:', e)
    showError(e.messages?.[0] || e.message || 'Failed to generate card. Make sure the event has an image uploaded.')
  } finally {
    inv._downloading = false
    await loadInvitations()
  }
}

function downloadQR(inv) {
  if (inv.qr_code_image) {
    window.open(inv.qr_code_image, '_blank')
  }
}

function formatDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString()
}

function statusBadge(status) {
  const classes = {
    'Draft': 'bg-gray-50 text-gray-600',
    'Ready': 'bg-blue-50 text-blue-700',
    'Sent': 'bg-green-50 text-green-700',
    'Delivered': 'bg-green-50 text-green-700',
    'Failed': 'bg-red-50 text-red-700',
    'Cancelled': 'bg-gray-100 text-gray-500',
  }
  return classes[status] || 'bg-gray-50 text-gray-600'
}

function deliveryBadge(status) {
  const classes = {
    'Pending': 'bg-gray-50 text-gray-600',
    'Sent': 'bg-blue-50 text-blue-700',
    'Delivered': 'bg-green-50 text-green-700',
    'Failed': 'bg-red-50 text-red-700',
  }
  return classes[status] || 'bg-gray-50 text-gray-600'
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
