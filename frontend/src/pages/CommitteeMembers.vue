<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Committee Members</h1>
        <p class="text-sm text-gray-500 mt-1">Manage roles and permissions for event staff</p>
      </div>
    </div>

    <!-- Event Selector -->
    <div class="bg-white rounded-lg border p-4 mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">Select Event</label>
      <FormControl type="select" v-model="selectedEvent" :options="eventOptions" />
    </div>

    <div v-if="!selectedEvent" class="text-center py-12 bg-white rounded-lg border">
      <FeatherIcon name="users" class="h-12 w-12 mx-auto mb-3 text-gray-300" />
      <p class="text-sm text-gray-500">Select an event to manage its committee members</p>
    </div>

    <div v-else>
      <!-- Add Member -->
      <div class="bg-white rounded-lg border p-4 mb-6">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Add Committee Member</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormControl type="select" v-model="newMember.user" :options="userOptions" placeholder="Select User" />
          <FormControl type="select" v-model="newMember.role" :options="roleOptions" />
          <Button @click="addMember" variant="solid" :loading="adding" iconLeft="plus" :label="__('Add Member')" />
        </div>
      </div>

      <!-- Members List -->
      <div class="bg-white rounded-lg border overflow-hidden">
        <table class="w-full">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Permissions</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="member in members" :key="member.name" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-sm text-gray-900">{{ member.user_name || member.user }}</td>
              <td class="px-4 py-3">
                <span class="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700">{{ member.role }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex gap-2 text-xs text-gray-500">
                  <span v-if="member.can_invite" class="text-green-600">Invite</span>
                  <span v-if="member.can_check_in" class="text-green-600">Check-In</span>
                  <span v-if="member.can_manage_guests" class="text-green-600">Guests</span>
                  <span v-if="member.can_manage_contributions" class="text-green-600">Contributions</span>
                </div>
              </td>
              <td class="px-4 py-3 text-right">
                <Button @click="confirmRemove(member)" variant="ghost" class="text-red-500 text-xs">Remove</Button>
              </td>
            </tr>
            <tr v-if="!members.length">
              <td colspan="4" class="px-4 py-8 text-center text-gray-500 text-sm">No committee members yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Remove Confirmation Dialog -->
    <Dialog :options="{ title: 'Remove Committee Member', size: 'sm' }" v-model="showRemoveDialog">
      <template #body-content>
        <div class="py-2">
          <div class="flex items-center gap-3 mb-3">
            <div class="h-10 w-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0">
              <FeatherIcon name="alert-triangle" class="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900">Remove {{ memberToRemove?.user_name || memberToRemove?.user }}?</p>
              <p class="text-xs text-gray-500 mt-0.5">This action cannot be undone. The member will lose all access to this event.</p>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showRemoveDialog = false" variant="ghost" size="sm">Cancel</Button>
        <Button @click="executeRemove" variant="solid" size="sm" :loading="removing" class="bg-red-600 hover:bg-red-700 text-white">
          Remove
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Dialog, FeatherIcon } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'

const events = ref([])
const members = ref([])
const users = ref([])
const selectedEvent = ref('')
const adding = ref(false)
const removing = ref(false)
const showRemoveDialog = ref(false)
const memberToRemove = ref(null)

const newMember = ref({
  user: '',
  role: 'Committee Member',
})

const roleOptions = [
  { label: 'Organizer', value: 'Organizer' },
  { label: 'Treasurer', value: 'Treasurer' },
  { label: 'Secretary', value: 'Secretary' },
  { label: 'Invitation Coordinator', value: 'Invitation Coordinator' },
  { label: 'Usher', value: 'Usher' },
  { label: 'Committee Member', value: 'Committee Member' },
  { label: 'Viewer', value: 'Viewer' },
]

const eventOptions = computed(() => {
  return [{ label: 'Select an event', value: '' }, ...(events.value || []).map(e => ({ label: e.event_name, value: e.name }))]
})

const userOptions = computed(() => {
  return [{ label: 'Select user', value: '' }, ...(users.value || []).map(u => ({ label: u.full_name || u.email || u.name, value: u.name }))]
})

onMounted(async () => {
  try {
    events.value = await frappeRequest({
      url: 'frappe.client.get_list',
      params: { doctype: 'Event', fields: ['name', 'event_name'], order_by: 'event_date DESC' },
    })
    users.value = await frappeRequest({
      url: 'frappe.client.get_list',
      params: { doctype: 'User', fields: ['name', 'full_name', 'email'], limit: 50 },
    })
  } catch (e) {
    console.error('Failed to load data:', e)
  }
})

// Auto-load committee members when selectedEvent changes
watch(selectedEvent, (newVal) => {
  if (newVal) {
    loadCommittee()
  } else {
    members.value = []
  }
})

async function loadCommittee() {
  if (!selectedEvent.value) return
  try {
    const data = await frappeRequest({
      url: 'invite.invite.doctype.committee_member.committee_member.get_event_committee',
      params: { event: selectedEvent.value },
    })
    members.value = data || []
  } catch (e) {
    console.error('Failed to load committee:', e)
  }
}

async function addMember() {
  if (!newMember.value.user || !selectedEvent.value) return
  adding.value = true
  try {
    await frappeRequest({
      url: 'frappe.client.save',
      params: {
        doc: JSON.stringify({
          doctype: 'Committee Member',
          event: selectedEvent.value,
          user: newMember.value.user,
          role: newMember.value.role,
        }),
      },
    })
    newMember.value = { user: '', role: 'Committee Member' }
    await loadCommittee()
  } catch (e) {
    console.error('Failed to add member:', e)
  } finally {
    adding.value = false
  }
}

function confirmRemove(member) {
  memberToRemove.value = member
  showRemoveDialog.value = true
}

async function executeRemove() {
  if (!memberToRemove.value) return
  removing.value = true
  try {
    await frappeRequest({
      url: 'frappe.client.delete',
      params: { doctype: 'Committee Member', name: memberToRemove.value.name },
    })
    showRemoveDialog.value = false
    memberToRemove.value = null
    await loadCommittee()
  } catch (e) {
    console.error('Failed to remove member:', e)
  } finally {
    removing.value = false
  }
}
</script>
