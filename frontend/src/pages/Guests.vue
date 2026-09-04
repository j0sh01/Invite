<template>
  <div>
    <EventWorkspaceHeader :event-id="props.eventId" />

    <!-- Content toolbar -->
    <div class="mb-5 mt-8 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="font-display text-xl text-gray-900">Guests</h2>
        <p class="mt-0.5 text-sm text-gray-500">{{ totalGuests }} guests for this event</p>
      </div>
      <div class="flex gap-2">
        <Button @click="showImportModal = true" variant="ghost" size="sm" iconLeft="upload" :label="__('Import')" class="hidden sm:inline-flex" />
        <Button @click="showImportModal = true" variant="ghost" size="sm" iconLeft="upload" class="sm:hidden" />
        <Button @click="showAddModal = true" variant="solid" size="sm" iconLeft="plus" :label="__('Add Guest')" />
      </div>
    </div>

    <!-- Search & Filters -->
    <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-4">
      <Input
        v-model="searchQuery"
        placeholder="Search guests..."
        class="flex-1"
        @input="searchGuests"
      />
      <div class="flex gap-3">
        <FormControl type="select" v-model="categoryFilter" :options="categoryOptions" class="w-full sm:w-40" placeholder="Category" />
        <FormControl type="select" v-model="rsvpFilter" :options="rsvpOptions" class="w-full sm:w-40" placeholder="RSVP Status" />
      </div>
    </div>

    <!-- Guests Table (responsive) -->
    <div class="bg-white rounded-lg border overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[800px]">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">Category</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">Card Scans</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">RSVP</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase hidden sm:table-cell">QR</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="guest in filteredGuests" :key="guest.name" class="hover:bg-gray-50">
              <td class="px-4 py-3">
                <p class="text-sm font-medium text-gray-900">{{ guest.full_name }}</p>
                <p v-if="guest.plus_one && guest.plus_one_name" class="text-xs text-gray-400">+1: {{ guest.plus_one_name }}</p>
              </td>
              <td class="px-4 py-3">
                <p class="text-sm text-gray-600">{{ guest.mobile_no || guest.phone || '-' }}</p>
                <p class="text-xs text-gray-400">{{ guest.email || '' }}</p>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <span class="text-sm text-gray-600">{{ guest.category || '-' }}</span>
              </td>
              <td class="px-4 py-3 hidden lg:table-cell">
                <span class="text-sm text-gray-600">{{ guest.number_of_attendees || 1 }} entr{{ (guest.number_of_attendees || 1) === 1 ? 'y' : 'ies' }}</span>
                <span v-if="guest.scans_used" class="ml-1 text-xs" :class="(guest.scans_used >= (guest.scans_allowed || 1)) ? 'text-red-500' : 'text-green-600'">
                  · {{ guest.scans_used }}/{{ guest.scans_allowed || 1 }} used
                </span>
              </td>
              <td class="px-4 py-3">
                <span :class="rsvpBadgeClass(guest.rsvp_status)" class="text-xs px-2 py-1 rounded-full">
                  {{ guest.rsvp_status || 'Pending' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1">
                  <FeatherIcon :name="guest.checked_in ? 'check-circle' : 'circle'" 
                    :class="guest.checked_in ? 'text-green-500' : 'text-gray-300'" class="h-4 w-4" />
                  <span class="text-xs text-gray-500 hidden sm:inline">{{ guest.checked_in ? 'Checked in' : 'Not checked in' }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-center hidden sm:table-cell">
                <button
                  @click="showGuestQR(guest)"
                  class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                  :title="__('View QR Code')"
                >
                  <FeatherIcon name="smartphone" class="h-4 w-4 text-gray-500" />
                </button>
              </td>
              <td class="px-4 py-3 text-right">
                <Button @click="editGuest(guest)" variant="ghost" class="text-xs">Edit</Button>
              </td>
            </tr>
            <tr v-if="!filteredGuests.length">
              <td colspan="10" class="px-4 py-12 text-center text-gray-500 text-sm">No guests found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Guest Modal -->
    <Dialog :options="{ title: 'Add Guest', size: 'lg' }" v-model="showAddModal">
      <template #body-content>
        <div class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="First Name" v-model="newGuest.first_name" required />
            <FormControl label="Last Name" v-model="newGuest.last_name" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Email" v-model="newGuest.email" />
            <FormControl label="Mobile No" v-model="newGuest.mobile_no" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Phone" v-model="newGuest.phone" />
            <FormControl label="Card Scans (people covered)" type="number" v-model="newGuest.number_of_attendees" />
            <p class="text-xs text-gray-400 -mt-2">How many people this card covers — the card can be scanned this many times (1 = single, 2 = double entry).</p>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Category" type="select" v-model="newGuest.category" :options="categoryOptionsForEdit" />
            <div></div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Plus One" type="checkbox" v-model="newGuest.plus_one" />
            <FormControl v-if="newGuest.plus_one" label="Plus One Name" v-model="newGuest.plus_one_name" />
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showAddModal = false" variant="ghost">Cancel</Button>
        <Button @click="addGuest" variant="solid" :loading="adding">Add Guest</Button>
      </template>
    </Dialog>

    <!-- Edit Guest Modal -->
    <Dialog :options="{ title: 'Edit Guest', size: 'lg' }" v-model="showEditModal">
      <template #body-content>
        <div class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="First Name" v-model="editGuestForm.first_name" required />
            <FormControl label="Last Name" v-model="editGuestForm.last_name" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Email" v-model="editGuestForm.email" />
            <FormControl label="Mobile No" v-model="editGuestForm.mobile_no" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Phone" v-model="editGuestForm.phone" />
            <FormControl label="Card Scans (people covered)" type="number" v-model="editGuestForm.number_of_attendees" />
            <p class="text-xs text-gray-400 -mt-2">How many people this card covers — the card can be scanned this many times (1 = single, 2 = double entry).</p>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Category" type="select" v-model="editGuestForm.category" :options="categoryOptionsForEdit" />
            <div></div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormControl label="Plus One" type="checkbox" v-model="editGuestForm.plus_one" />
            <FormControl v-if="editGuestForm.plus_one" label="Plus One Name" v-model="editGuestForm.plus_one_name" />
          </div>
          <FormControl label="RSVP Status" type="select" v-model="editGuestForm.rsvp_status" :options="rsvpStatusOptions" />
        </div>
      </template>
      <template #actions>
        <Button @click="showEditModal = false" variant="ghost">Cancel</Button>
        <Button @click="updateGuest" variant="solid" size="sm" :loading="updating" iconLeft="check" :label="__('Save Changes')" />
      </template>
    </Dialog>

    <!-- Import Modal -->
    <Dialog :options="{ title: 'Import Guests' }" v-model="showImportModal">
      <template #body-content>
        <div class="space-y-5">
          <!-- Step 1: Download Template -->
          <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h4 class="text-sm font-medium text-blue-800 mb-1">Step 1: Download Template</h4>
            <p class="text-xs text-blue-600 mb-3">Get a CSV template with the correct columns for guest data.</p>
            <Button @click="downloadTemplate" variant="ghost" size="sm" :loading="downloadingTemplate" iconLeft="download" :label="__('Download CSV Template')" />
          </div>

          <!-- Step 2: Upload File -->
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h4 class="text-sm font-medium text-gray-800 mb-1">Step 2: Upload Your File</h4>
            <p class="text-xs text-gray-500 mb-3">Fill in the template and upload it here (CSV or Excel files accepted).</p>
            <div
              class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 transition-colors"
              @click="triggerFileInput"
              @dragover.prevent="dragOver = true"
              @dragleave.prevent="dragOver = false"
              @drop.prevent="handleFileDrop"
              :class="dragOver ? 'border-blue-400 bg-blue-50' : ''"
            >
              <FeatherIcon name="upload" class="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p class="text-sm text-gray-600">
                <span class="text-blue-600 font-medium">Click to browse</span>
                <span v-if="!selectedFile"> or drag & drop here</span>
              </p>
              <p v-if="!selectedFile" class="text-xs text-gray-400 mt-1">CSV or Excel (.xlsx) files</p>
              <div v-if="selectedFile" class="mt-2 flex items-center justify-center gap-2 text-sm text-gray-700">
                <FeatherIcon name="file-text" class="h-4 w-4 text-blue-500" />
                <span class="font-medium">{{ selectedFile.name }}</span>
                <span class="text-gray-400">({{ formatFileSize(selectedFile.size) }})</span>
                <button @click.stop="selectedFile = null" class="text-red-500 hover:text-red-700 ml-1">
                  <FeatherIcon name="x" class="h-4 w-4" />
                </button>
              </div>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept=".csv,.xlsx,.xls"
              class="hidden"
              @change="handleFileSelect"
            />
          </div>

          <!-- Import Results -->
          <div v-if="importResult" class="rounded-lg p-4" :class="importResult.error_count ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'">
            <div class="flex items-center gap-2 mb-2">
              <FeatherIcon :name="importResult.error_count ? 'alert-triangle' : 'check-circle'" 
                :class="importResult.error_count ? 'text-amber-500' : 'text-green-500'" class="h-5 w-5" />
              <span class="text-sm font-medium" :class="importResult.error_count ? 'text-amber-800' : 'text-green-800'">
                {{ importResult.success_count }} imported, {{ importResult.error_count }} errors
              </span>
            </div>
            <div v-if="importResult.errors?.length" class="space-y-1 max-h-32 overflow-y-auto">
              <p v-for="err in importResult.errors" :key="err.row" class="text-xs text-red-600">
                Row {{ err.row }}: {{ err.error }}
              </p>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="showImportModal = false; importResult = null; selectedFile = null" variant="ghost" size="sm">Cancel</Button>
        <Button @click="importGuests" variant="solid" size="sm" :loading="importing" :disabled="!selectedFile" iconLeft="upload" :label="__('Import Guests')" />
      </template>
    </Dialog>

    <!-- QR Code Modal -->
    <Dialog :options="{ title: selectedGuest?.full_name || 'QR Code' }" v-model="showQRModal">
      <template #body-content>
        <div class="py-4 text-center space-y-4">
          <div class="bg-white rounded-lg border p-4 inline-block mx-auto">
            <img
              v-if="qrCodeImage"
              :src="qrCodeImage"
              class="w-48 h-48 mx-auto"
              alt="QR Code"
            />
            <div v-else class="w-48 h-48 mx-auto bg-gray-50 rounded-lg flex items-center justify-center">
              <FeatherIcon name="smartphone" class="h-12 w-12 text-gray-300" />
            </div>
          </div>
          <div v-if="selectedGuest" class="text-sm text-gray-600">
            <p class="font-medium text-gray-900">{{ selectedGuest.full_name }}</p>
            <p class="text-xs mt-1">
              Code: {{ selectedGuest.invite_code }}
            </p>
            <p class="text-xs text-gray-400 mt-1">
              Card scans allowed: {{ selectedGuest.number_of_attendees || 1 }}
              <span v-if="selectedGuest.scans_used" :class="selectedGuest.scans_used >= (selectedGuest.scans_allowed || 1) ? 'text-red-500' : 'text-green-600'">
                · {{ selectedGuest.scans_used }}/{{ selectedGuest.scans_allowed || 1 }} used
              </span>
            </p>
          </div>
        </div>
      </template>
      <template #actions>
        <Button @click="generateGuestQR" variant="solid" size="sm" :loading="generatingQR" iconLeft="smartphone" :label="__('Generate QR')" />
        <Button @click="showQRModal = false" variant="ghost" size="sm">{{ __('Close') }}</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from '@/utils/api'
import EventWorkspaceHeader from '@/components/EventWorkspaceHeader.vue'

const props = defineProps({ eventId: String })

const guests = ref([])
const totalGuests = ref(0)
const searchQuery = ref('')
const categoryFilter = ref('')
const rsvpFilter = ref('')
const showAddModal = ref(false)
const showEditModal = ref(false)
const showImportModal = ref(false)
const adding = ref(false)
const updating = ref(false)
const importing = ref(false)
const categories = ref([])
const rsvpStatuses = ref([])

const newGuest = ref({
  first_name: '',
  last_name: '',
  email: '',
  mobile_no: '',
  phone: '',
  category: '',
  plus_one: 0,
  plus_one_name: '',
  number_of_attendees: 1,
})

const editGuestForm = ref({
  first_name: '',
  last_name: '',
  email: '',
  mobile_no: '',
  phone: '',
  category: '',
  plus_one: 0,
  plus_one_name: '',
  number_of_attendees: 1,
  rsvp_status: '',
})

const editingGuestName = ref(null)

const showQRModal = ref(false)
const selectedGuest = ref(null)
const qrCodeImage = ref('')
const generatingQR = ref(false)

const importData = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)
const dragOver = ref(false)
const downloadingTemplate = ref(false)
const importResult = ref(null)

const categoryOptionsForEdit = computed(() => {
  return [{ label: 'None', value: '' }, ...(categories.value?.map(c => ({ label: c.category_name, value: c.category_name })) || [])]
})

const rsvpStatusOptions = computed(() => {
  return [{ label: 'Pending', value: '' }, 'Accepted', 'Declined', 'Maybe'].map(s => typeof s === 'string' ? ({ label: s, value: s }) : s)
})

const categoryOptions = computed(() => {
  return [{ label: 'All Categories', value: '' }, ...(categories.value?.map(c => ({ label: c.category_name, value: c.category_name })) || [])]
})

const rsvpOptions = computed(() => {
  return [{ label: 'All RSVPs', value: '' }, ...(rsvpStatuses.value || []).map(s => ({ label: s.status, value: s.status }))]
})

const filteredGuests = computed(() => {
  let result = guests.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(g => 
      (g.full_name && g.full_name.toLowerCase().includes(q)) ||
      (g.email && g.email.toLowerCase().includes(q)) ||
      (g.mobile_no && g.mobile_no.includes(q))
    )
  }
  if (categoryFilter.value) {
    result = result.filter(g => g.category === categoryFilter.value)
  }
  if (rsvpFilter.value) {
    result = result.filter(g => g.rsvp_status === rsvpFilter.value)
  }
  return result
})

onMounted(async () => {
  await Promise.all([loadGuests(), loadCategories(), loadOptions()])
})

async function loadGuests() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.guest.get_list',
      params: { event: props.eventId },
    })
    guests.value = data.guests || []
    totalGuests.value = data.total || 0
  } catch (e) {
    console.error('Failed to load guests:', e)
  }
}

async function loadCategories() {
  try {
    categories.value = await frappeRequest({
      url: 'frappe.client.get_list',
      params: { doctype: 'Guest Category', fields: ['category_name'], order_by: 'position ASC' },
    })
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
}

async function loadOptions() {
  try {
    const data = await frappeRequest({
      url: 'invite.api.event.get_options',
    })
    rsvpStatuses.value = (data.rsvp_statuses || []).map(s => ({ status: s }))
  } catch (e) {
    console.error('Failed to load options:', e)
  }
}


async function addGuest() {
  adding.value = true
  try {
    await frappeRequest({
      url: 'invite.api.guest.create',
      params: { data: JSON.stringify({ ...newGuest.value, event: props.eventId }) },
    })
    showAddModal.value = false
    newGuest.value = { first_name: '', last_name: '', email: '', mobile_no: '', phone: '', category: '', plus_one: 0, plus_one_name: '', number_of_attendees: 1 }
    await loadGuests()
  } catch (e) {
    console.error('Failed to add guest:', e)
  } finally {
    adding.value = false
  }
}

async function downloadTemplate() {
  downloadingTemplate.value = true
  try {
    const res = await fetch('/api/method/invite.api.guest.download_template', {
      headers: {
        'X-Frappe-CSRF-Token': window.csrf_token || '',
        'X-Frappe-Site-Name': window.location.hostname,
      },
    })
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'guest_import_template.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Failed to download template:', e)
  } finally {
    downloadingTemplate.value = false
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (file) {
    selectedFile.value = file
    importResult.value = null
  }
}

function handleFileDrop(event) {
  dragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
    selectedFile.value = file
    importResult.value = null
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function importGuests() {
  if (!selectedFile.value) return
  importing.value = true
  importResult.value = null
  try {
    // Upload the file using native fetch (frappeRequest doesn't support FormData body)
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('doctype', 'Guest')
    formData.append('docname', props.eventId)
    formData.append('is_private', '0')

    const uploadRes = await fetch('/api/method/upload_file', {
      method: 'POST',
      headers: {
        'X-Frappe-CSRF-Token': window.csrf_token || '',
        'X-Frappe-Site-Name': window.location.hostname,
      },
      body: formData,
    })

    const uploadData = await uploadRes.json()
    const fileUrl = uploadData?.message?.file_url
    if (!fileUrl) {
      throw new Error(uploadData?._error_message || 'File upload failed')
    }

    // Import from the uploaded file
    const result = await frappeRequest({
      url: 'invite.api.guest.import_from_csv',
      params: { event: props.eventId, file_url: fileUrl },
    })
    
    importResult.value = result
    if (result?.created?.length) {
      await loadGuests()
    }
  } catch (e) {
    console.error('Failed to import guests:', e)
    importResult.value = { errors: [{ row: 0, error: e.message || 'Import failed' }], success_count: 0, error_count: 1 }
  } finally {
    importing.value = false
  }
}

function showGuestQR(guest) {
  selectedGuest.value = guest
  qrCodeImage.value = guest.qr_code_image || guest.qr_code || ''
  showQRModal.value = true
}

async function generateGuestQR() {
  if (!selectedGuest.value) return
  generatingQR.value = true
  try {
    // Find the invitation for this guest
    const data = await frappeRequest({
      url: 'invite.api.invitation.get_list',
      params: { event: props.eventId },
    })
    const inv = (data.invitations || []).find(i => i.guest === selectedGuest.value.name)
    if (inv) {
      const result = await frappeRequest({
        url: 'invite.api.invitation.generate_qr',
        params: { invitation: inv.name },
      })
      qrCodeImage.value = result.qr_code_url
    }
    await loadGuests()
  } catch (e) {
    console.error('Failed to generate QR:', e)
  } finally {
    generatingQR.value = false
  }
}


function editGuest(guest) {
  editingGuestName.value = guest.name
  editGuestForm.value = {
    first_name: guest.first_name || '',
    last_name: guest.last_name || '',
    email: guest.email || '',
    mobile_no: guest.mobile_no || '',
    phone: guest.phone || '',
    category: guest.category || '',
    plus_one: guest.plus_one || 0,
    plus_one_name: guest.plus_one_name || '',
    number_of_attendees: guest.number_of_attendees || 1,
    rsvp_status: guest.rsvp_status || '',
  }
  showEditModal.value = true
}

async function updateGuest() {
  updating.value = true
  try {
    await frappeRequest({
      url: 'invite.api.guest.update',
      params: { 
        guest: editingGuestName.value,
        data: JSON.stringify(editGuestForm.value),
      },
    })
    showEditModal.value = false
    await loadGuests()
  } catch (e) {
    console.error('Failed to update guest:', e)
  } finally {
    updating.value = false
  }
}

function formatCurrency(amount) {
  if (!amount) return 'TZS 0'
  return `TZS ${Number(amount).toLocaleString()}`
}

function rsvpBadgeClass(status) {
  const classes = {
    'Accepted': 'bg-green-50 text-green-700',
    'Declined': 'bg-red-50 text-red-700',
    'Pending': 'bg-gray-50 text-gray-600',
    'Maybe': 'bg-amber-50 text-amber-700',
  }
  return classes[status] || 'bg-gray-50 text-gray-600'
}
</script>
