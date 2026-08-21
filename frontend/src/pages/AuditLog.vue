<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl sm:text-2xl font-semibold text-gray-900">Audit Log</h1>
        <p class="text-sm text-gray-500 mt-1">{{ totalLogs }} activities recorded</p>
      </div>
      <div class="flex gap-2">
        <Button @click="exportLogs" variant="ghost" size="sm" iconLeft="download" :label="__('Export')" />
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-lg border p-4 mb-4">
      <div class="flex flex-col sm:flex-row gap-3">
        <Input
          v-model="searchQuery"
          placeholder="Search logs..."
          class="flex-1"
        />
        <div class="flex gap-3">
          <FormControl type="select" v-model="categoryFilter" :options="categoryOptions" class="w-full sm:w-44" />
          <FormControl type="select" v-model="actionFilter" :options="actionOptions" class="w-full sm:w-52" />
        </div>
      </div>
    </div>

    <!-- Stats summary -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
      <div v-for="cat in statsSummary" :key="cat.category" class="bg-white rounded-lg border p-3 text-center">
        <p class="text-lg font-semibold text-gray-900">{{ cat.count }}</p>
        <p class="text-[10px] sm:text-xs text-gray-500">{{ cat.category }}</p>
      </div>
    </div>

    <!-- Logs table -->
    <div class="bg-white rounded-lg border overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[700px]">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Guest</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">Details</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden sm:table-cell">By</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="log in filteredLogs" :key="log.name" class="hover:bg-gray-50">
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span :class="categoryBadge(log.action_category)" class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium">
                    {{ log.action_category }}
                  </span>
                  <span class="text-xs text-gray-700 truncate max-w-[140px]">{{ log.action_type }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <p v-if="log.guest_name" class="text-sm text-gray-900 truncate max-w-[140px]">{{ log.guest_name }}</p>
                <p v-else class="text-sm text-gray-400">-</p>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <p class="text-xs text-gray-600 truncate max-w-[220px]">{{ log.subject }}</p>
              </td>
              <td class="px-4 py-3 hidden sm:table-cell">
                <p class="text-xs text-gray-600 truncate max-w-[100px]">{{ log.performed_by_name || log.performed_by }}</p>
              </td>
              <td class="px-4 py-3">
                <p class="text-xs text-gray-500 whitespace-nowrap">{{ formatDateTime(log.creation) }}</p>
              </td>
            </tr>
            <tr v-if="!filteredLogs.length">
              <td colspan="5" class="px-4 py-12 text-center text-gray-500 text-sm">
                No activity logs found
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Load more -->
      <div v-if="filteredLogs.length < totalLogs" class="px-4 py-3 border-t text-center">
        <Button @click="loadMore" variant="ghost" size="sm" :loading="loading">
          Load More ({{ filteredLogs.length }} of {{ totalLogs }})
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from '@/utils/api'

const props = defineProps({ eventId: { type: String, default: null } })

const logs = ref([])
const totalLogs = ref(0)
const loading = ref(false)
const searchQuery = ref('')
const categoryFilter = ref('')
const actionFilter = ref([])

const categories = ref([])

const categoryOptions = computed(() => [
  { label: 'All Categories', value: '' },
  ...categories.value.map(c => ({ label: c, value: c })),
])

const actionOptions = computed(() => {
  const types = [...new Set(logs.value.map(l => l.action_type))].sort()
  return [
    { label: 'All Actions', value: '' },
    ...types.map(t => ({ label: t, value: t })),
  ]
})

const filteredLogs = computed(() => {
  let result = logs.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(l =>
      (l.guest_name && l.guest_name.toLowerCase().includes(q)) ||
      (l.subject && l.subject.toLowerCase().includes(q)) ||
      (l.action_type && l.action_type.toLowerCase().includes(q))
    )
  }
  if (categoryFilter.value) {
    result = result.filter(l => l.action_category === categoryFilter.value)
  }
  if (actionFilter.value) {
    result = result.filter(l => l.action_type === actionFilter.value)
  }
  return result
})

const statsSummary = computed(() => {
  const counts = {}
  for (const log of logs.value) {
    counts[log.action_category] = (counts[log.action_category] || 0) + 1
  }
  return Object.entries(counts)
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count)
})

onMounted(async () => {
  await Promise.all([loadLogs(), loadCategories()])
})

async function loadLogs(offset = 0) {
  loading.value = true
  try {
    const params = { limit: 100, offset }
    if (props.eventId) params.event = props.eventId
    const data = await frappeRequest({
      url: 'invite.api.activity_log.get_logs',
      params,
    })
    if (offset === 0) {
      logs.value = data.logs || []
    } else {
      logs.value = [...logs.value, ...(data.logs || [])]
    }
    totalLogs.value = data.total || 0
  } catch (e) {
    console.error('Failed to load logs:', e)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  await loadLogs(logs.value.length)
}

async function loadCategories() {
  try {
    categories.value = await frappeRequest({
      url: 'invite.api.activity_log.get_categories',
    })
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
}

async function exportLogs() {
  const headers = ['Time', 'Action', 'Category', 'Guest', 'Subject', 'By']
  const rows = filteredLogs.value.map(l => [
    formatDateTime(l.creation),
    l.action_type,
    l.action_category,
    l.guest_name || '',
    l.subject || '',
    l.performed_by_name || l.performed_by || '',
  ])
  const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit_log_${props.eventId || 'all'}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}

function formatDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString()
}

function categoryBadge(category) {
  const classes = {
    'Guest Management': 'bg-blue-50 text-blue-700',
    'Invitation': 'bg-purple-50 text-purple-700',
    'Check-In': 'bg-green-50 text-green-700',
    'RSVP': 'bg-indigo-50 text-indigo-700',
    'Communication': 'bg-orange-50 text-orange-700',
    'Card': 'bg-pink-50 text-pink-700',
    'Frontdesk': 'bg-cyan-50 text-cyan-700',
    'System': 'bg-gray-50 text-gray-600',
  }
  return classes[category] || 'bg-gray-50 text-gray-600'
}
</script>
