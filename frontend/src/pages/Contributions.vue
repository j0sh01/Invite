<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Contributions</h1>
        <p class="text-sm text-gray-500 mt-1">Track pledges and payments for this event</p>
      </div>
      <Button @click="showAddModal = true" variant="solid" size="sm" iconLeft="plus" :label="__('Record Contribution')" />
    </div>

    <!-- Sub-navigation Tabs -->
    <EventTabs :eventId="props.eventId" />

    <!-- Summary Cards -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg border p-4">
        <p class="text-xs text-gray-500 mb-1">Total Pledged</p>
        <p class="text-xl font-semibold text-gray-900">{{ formatCurrency(summary.total_pledged) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-4">
        <p class="text-xs text-gray-500 mb-1">Total Paid</p>
        <p class="text-xl font-semibold text-green-600">{{ formatCurrency(summary.total_paid) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-4">
        <p class="text-xs text-gray-500 mb-1">Outstanding</p>
        <p class="text-xl font-semibold text-amber-600">{{ formatCurrency(summary.total_outstanding) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-4">
        <p class="text-xs text-gray-500 mb-1">Collection Rate</p>
        <p class="text-xl font-semibold text-blue-600">{{ summary.collection_rate || 0 }}%</p>
      </div>
    </div>

    <!-- Distribution by Type -->
    <div v-if="summary.by_type" class="grid grid-cols-2 gap-4 mb-6">
      <div v-for="(data, type) in summary.by_type" :key="type" class="bg-white rounded-lg border p-4">
        <p class="text-sm font-medium text-gray-900 mb-2">{{ type }}</p>
        <div class="flex justify-between text-sm">
          <span class="text-gray-500">Pledged: {{ formatCurrency(data.pledged) }}</span>
          <span class="text-gray-500">Paid: {{ formatCurrency(data.paid) }}</span>
          <span class="text-gray-500">Count: {{ data.count }}</span>
        </div>
      </div>
    </div>

    <!-- Contributions List -->
    <div class="bg-white rounded-lg border overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Guest</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Pledged</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Paid</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Outstanding</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="c in contributions" :key="c.name" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm text-gray-900">{{ c.guest_name }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ c.contribution_type }}</td>
            <td class="px-4 py-3 text-sm text-gray-900 text-right">{{ formatCurrency(c.pledged_amount) }}</td>
            <td class="px-4 py-3 text-sm text-green-600 text-right">{{ formatCurrency(c.paid_amount) }}</td>
            <td class="px-4 py-3 text-sm text-amber-600 text-right">{{ formatCurrency(c.outstanding_amount) }}</td>
            <td class="px-4 py-3">
              <span :class="statusBadge(c.payment_status)" class="text-xs px-2 py-1 rounded-full">{{ c.payment_status }}</span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ c.payment_method || '-' }}</td>
            <td class="px-4 py-3 text-right">
              <Button @click="recordPayment(c)" variant="ghost" class="text-xs">Record Payment</Button>
            </td>
          </tr>
          <tr v-if="!contributions.length">
            <td colspan="8" class="px-4 py-12 text-center text-gray-500 text-sm">No contributions recorded yet</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Contribution Modal -->
    <Dialog :options="{ title: 'Record Contribution' }" v-model="showAddModal">
      <template #body-content>
        <div class="space-y-4">
          <FormControl label="Guest" type="select" v-model="newContrib.guest" :options="guestOptions" required />
          <FormControl label="Contribution Type" type="select" v-model="newContrib.contribution_type" :options="contributionTypeOptions" required />
          <FormControl label="Type" type="select" v-model="newContrib.type" :options="[{ label: 'Pledge', value: 'Pledge' }, { label: 'Payment', value: 'Payment' }, { label: 'Partial Payment', value: 'Partial Payment' }]" />
          <div class="grid grid-cols-2 gap-4">
            <FormControl label="Pledged Amount" type="number" v-model="newContrib.pledged_amount" />
            <FormControl label="Paid Amount" type="number" v-model="newContrib.paid_amount" />
          </div>
          <FormControl label="Payment Method" type="select" v-model="newContrib.payment_method" :options="paymentMethodOptions" />
          <FormControl label="Transaction Reference" v-model="newContrib.transaction_reference" />
        </div>
      </template>
      <template #actions>
        <Button @click="showAddModal = false" variant="ghost">Cancel</Button>
        <Button @click="addContribution" variant="solid" :loading="adding">Save</Button>
      </template>
    </Dialog>

    <!-- Record Payment Modal (replaces browser prompt) -->
    <Dialog :options="{ title: 'Record Payment' }" v-model="showPaymentModal">
      <template #body-content>
        <div class="space-y-4 py-2">
          <div class="bg-gray-50 rounded-lg p-3 text-sm">
            <div class="flex justify-between mb-1">
              <span class="text-gray-500">Guest:</span>
              <span class="font-medium text-gray-900">{{ paymentForm.guest_name }}</span>
            </div>
            <div class="flex justify-between mb-1">
              <span class="text-gray-500">Pledged:</span>
              <span class="font-medium text-gray-900">{{ formatCurrency(paymentForm.pledged) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Outstanding:</span>
              <span class="font-medium text-amber-600">{{ formatCurrency(paymentForm.outstanding) }}</span>
            </div>
          </div>
          <FormControl label="Payment Amount" type="number" v-model="paymentForm.amount" required />
          <FormControl label="Payment Method" type="select" v-model="paymentForm.method" :options="paymentMethodOptions" />
          <FormControl label="Transaction Reference" v-model="paymentForm.reference" />
        </div>
      </template>
      <template #actions>
        <Button @click="showPaymentModal = false" variant="ghost" size="sm">Cancel</Button>
        <Button @click="submitPayment" variant="solid" size="sm" :loading="paying" :disabled="!paymentForm.amount">
          Record Payment
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from '@/utils/api'
import EventTabs from '@/components/EventTabs.vue'

const props = defineProps({ eventId: String })

const contributions = ref([])
const summary = ref({})
const guests = ref([])
const contributionTypes = ref([])
const showAddModal = ref(false)
const showPaymentModal = ref(false)
const adding = ref(false)
const paying = ref(false)

const paymentForm = ref({
  contribution: null,
  guest_name: '',
  pledged: 0,
  outstanding: 0,
  amount: 0,
  method: '',
  reference: '',
})

const newContrib = ref({
  guest: '',
  contribution_type: '',
  type: 'Pledge',
  pledged_amount: 0,
  paid_amount: 0,
  payment_method: '',
  transaction_reference: '',
  event: props.eventId,
})

const guestOptions = computed(() => {
  return (guests.value || []).map(g => ({ label: g.full_name || g.name, value: g.name }))
})

const contributionTypeOptions = computed(() => {
  return (contributionTypes.value || []).map(t => ({ label: t.type_name, value: t.type_name }))
})

const paymentMethodOptions = [
  { label: 'Select', value: '' },
  { label: 'Cash', value: 'Cash' },
  { label: 'Mobile Money', value: 'Mobile Money' },
  { label: 'Bank Transfer', value: 'Bank Transfer' },
  { label: 'Cheque', value: 'Cheque' },
  { label: 'In-Kind', value: 'In-Kind' },
  { label: 'Other', value: 'Other' },
]

onMounted(async () => {
  await Promise.all([loadContributions(), loadGuests(), loadContributionTypes()])
})

async function loadContributions() {
  try {
    const [data, sum] = await Promise.all([
      frappeRequest({ url: 'invite.api.contribution.get_list', params: { event: props.eventId } }),
      frappeRequest({ url: 'invite.api.contribution.get_summary', params: { event: props.eventId } }),
    ])
    contributions.value = data.contributions || []
    summary.value = sum || {}
  } catch (e) {
    console.error('Failed to load contributions:', e)
  }
}

async function loadGuests() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.guest.get_list',
      params: { event: props.eventId },
    })
    guests.value = data.guests || []
  } catch (e) {
    console.error('Failed to load guests:', e)
  }
}

async function loadContributionTypes() {
  try {
    contributionTypes.value = await frappeRequest({
      url: 'frappe.client.get_list',
      params: { doctype: 'Contribution Type', fields: ['type_name', 'is_cash'], order_by: 'position ASC' },
    })
  } catch (e) {
    console.error('Failed to load contribution types:', e)
  }
}

async function addContribution() {
  adding.value = true
  try {
    await frappeRequest({
      url: 'invite.api.contribution.create',
      params: { data: JSON.stringify(newContrib.value) },
    })
    showAddModal.value = false
    newContrib.value = { guest: '', contribution_type: '', type: 'Pledge', pledged_amount: 0, paid_amount: 0, payment_method: '', transaction_reference: '', event: props.eventId }
    await loadContributions()
  } catch (e) {
    console.error('Failed to add contribution:', e)
  } finally {
    adding.value = false
  }
}

function recordPayment(c) {
  paymentForm.value = {
    contribution: c.name,
    guest_name: c.guest_name,
    pledged: c.pledged_amount || 0,
    outstanding: c.outstanding_amount || 0,
    amount: c.outstanding_amount || '',
    method: '',
    reference: '',
  }
  showPaymentModal.value = true
}

async function submitPayment() {
  paying.value = true
  try {
    await frappeRequest({
      url: 'invite.invite.doctype.contribution.contribution.reconcile_contribution',
      params: {
        contribution: paymentForm.value.contribution,
        paid_amount: paymentForm.value.amount,
        payment_method: paymentForm.value.method || null,
        transaction_reference: paymentForm.value.reference || null,
      },
    })
    showPaymentModal.value = false
    await loadContributions()
  } catch (e) {
    console.error('Failed to record payment:', e)
  } finally {
    paying.value = false
  }
}

function formatCurrency(amount) {
  if (!amount) return 'TZS 0'
  return `TZS ${Number(amount).toLocaleString()}`
}

function statusBadge(status) {
  const classes = {
    'Pending': 'bg-gray-50 text-gray-600',
    'Partially Paid': 'bg-amber-50 text-amber-700',
    'Paid': 'bg-green-50 text-green-700',
    'Cancelled': 'bg-red-50 text-red-700',
  }
  return classes[status] || 'bg-gray-50 text-gray-600'
}
</script>
