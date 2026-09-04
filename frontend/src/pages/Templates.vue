<template>
  <div class="max-w-6xl mx-auto">
    <!-- Page header -->
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="font-display text-3xl text-gray-900">Invitation Templates</h1>
        <p class="mt-1 text-sm text-gray-500">
          Design the invitation cards your guests receive — the event photo and each guest's QR code are placed automatically.
        </p>
      </div>
      <Button variant="solid" iconLeft="plus" :label="__('New Template')" @click="openCreate" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-gray-500">Loading templates...</div>

    <!-- Empty state -->
    <div v-else-if="!templates.length" class="bg-white border border-hairline rounded-xl p-12 text-center">
      <FeatherIcon name="layout" class="h-12 w-12 mx-auto text-gray-300 mb-3" />
      <h2 class="font-display text-xl text-gray-900 mb-1">No templates yet</h2>
      <p class="text-sm text-gray-500 mb-6">Create your first invitation card template.</p>
      <Button variant="solid" iconLeft="plus" :label="__('Create Template')" @click="openCreate" />
    </div>

    <!-- Template grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="t in templates"
        :key="t.name"
        class="group bg-white border border-hairline rounded-xl overflow-hidden hover:shadow-md transition-shadow"
      >
        <!-- Mini preview -->
        <div class="h-40 bg-gradient-to-br from-[#f5efe2] to-[#ece2cf] relative overflow-hidden">
          <div class="absolute inset-0 flex items-center justify-center px-6">
            <div
              class="w-24 bg-white border border-[#e5ddcd] rounded-sm shadow-sm text-center py-3"
              :style="{ borderColor: t.primary_color }"
            >
              <p class="text-[8px] uppercase tracking-[0.18em] text-gray-400 mb-1">Invitation</p>
              <p class="text-[11px] font-display text-gray-800 truncate px-1">{{ t.title }}</p>
              <div class="mt-2 mx-auto w-6 h-6 grid place-items-center" :style="{ background: t.accent_color, color: '#fff' }">
                <FeatherIcon name="grid" class="h-3 w-3" />
              </div>
            </div>
          </div>
          <span
            v-if="t.is_default"
            class="absolute top-2 left-2 inline-flex items-center gap-1 rounded-full bg-ink text-white text-[10px] px-2 py-0.5"
          >
            <FeatherIcon name="star" class="h-3 w-3" /> Default
          </span>
          <span
            v-if="!t.enabled"
            class="absolute top-2 right-2 rounded-full bg-gray-200 text-gray-600 text-[10px] px-2 py-0.5"
          >
            Disabled
          </span>
        </div>

        <!-- Details -->
        <div class="p-4">
          <div class="flex items-center justify-between gap-2">
            <h3 class="font-medium text-gray-900 truncate">{{ t.title }}</h3>
            <span class="text-[10px] uppercase tracking-wider text-[#8F3B1C] bg-[#8F3B1C]/10 rounded-full px-2 py-0.5">
              {{ t.layout }}
            </span>
          </div>
          <p class="text-xs text-gray-500 mt-1 truncate">{{ t.template_name }}</p>

          <div class="flex items-center gap-3 mt-3">
            <div class="flex items-center gap-1">
              <span class="w-4 h-4 rounded-full border border-black/10" :style="{ background: t.primary_color }" title="Primary color" />
              <span class="w-4 h-4 rounded-full border border-black/10" :style="{ background: t.accent_color }" title="Accent color" />
            </div>
            <div class="text-[11px] text-gray-500 flex items-center gap-3">
              <span class="inline-flex items-center gap-1"><FeatherIcon name="image" class="h-3 w-3" /> {{ t.image_position }}</span>
              <span class="inline-flex items-center gap-1"><FeatherIcon name="grid" class="h-3 w-3" /> {{ t.qr_position }}</span>
            </div>
          </div>

          <div class="flex gap-2 mt-4 pt-3 border-t border-hairline">
            <Button variant="ghost" size="sm" iconLeft="edit-2" :label="__('Edit')" class="flex-1" @click="openEdit(t)" />
            <Button variant="ghost" size="sm" iconLeft="trash-2" class="flex-1 text-red-600" :label="__('Delete')" @click="removeTemplate(t)" />
          </div>
        </div>
      </div>
    </div>

    <!-- Create / Edit dialog -->
    <Dialog :options="{ title: editing ? 'Edit Template' : 'New Template', size: '3xl' }" v-model="showDialog">
      <template #body-content>
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 py-2">
          <!-- Form -->
          <div class="lg:col-span-3 space-y-4">
            <FormControl label="Template Name" v-model="form.template_name" required placeholder="e.g. Classic Wedding" />
            <FormControl label="Title" v-model="form.title" required placeholder="Shown on the card and in lists" />

            <div class="grid grid-cols-2 gap-4">
              <FormControl label="Layout" type="select" v-model="form.layout" :options="layoutOptions" />
              <FormControl label="QR Code Position" type="select" v-model="form.qr_position" :options="qrPositionOptions" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1.5">Primary Color</label>
                <div class="flex items-center gap-2">
                  <input type="color" v-model="form.primary_color" class="h-9 w-14 rounded border border-hairline bg-white cursor-pointer" />
                  <span class="text-xs font-mono text-gray-500">{{ form.primary_color }}</span>
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1.5">Accent Color</label>
                <div class="flex items-center gap-2">
                  <input type="color" v-model="form.accent_color" class="h-9 w-14 rounded border border-hairline bg-white cursor-pointer" />
                  <span class="text-xs font-mono text-gray-500">{{ form.accent_color }}</span>
                </div>
              </div>
            </div>

            <FormControl label="Image Position" type="select" v-model="form.image_position" :options="imagePositionOptions" />

            <FormControl
              label="Invitation Wording"
              type="textarea"
              v-model="form.invitation_message"
              description="Use {guest_name}, {event_name}, {event_date}, {event_time}, {venue}"
              class="w-full"
            />

            <div class="flex items-center gap-6">
              <FormControl type="checkbox" label="Enabled" v-model="form.enabled" />
              <FormControl type="checkbox" label="Default Template" v-model="form.is_default" />
            </div>
          </div>

          <!-- Live preview -->
          <div class="lg:col-span-2">
            <p class="text-xs font-medium text-gray-600 mb-2">Live preview</p>
            <div class="relative overflow-hidden rounded-lg border border-hairline shadow-sm mx-auto" style="max-width: 220px; aspect-ratio: 210/297; background: #fffdf8">
              <!-- Cover image -->
              <template v-if="form.image_position === 'Cover'">
                <div class="absolute inset-0 bg-gradient-to-br from-[#8F3B1C]/80 to-[#2b2118]/90"></div>
              </template>

              <!-- Side image -->
              <template v-else-if="form.image_position === 'Left' || form.image_position === 'Right'">
                <div
                  class="absolute top-0 h-full w-[34%] bg-gradient-to-b from-[#d9c9a8] to-[#b9a17a]"
                  :class="form.image_position === 'Left' ? 'left-0' : 'right-0'"
                >
                  <div class="h-full grid place-items-center text-white/70">
                    <FeatherIcon name="user" class="h-8 w-8" />
                  </div>
                </div>
              </template>

              <!-- Top image -->
              <template v-else>
                <div class="h-24 bg-gradient-to-b from-[#d9c9a8] to-[#c0a87e] grid place-items-center text-white/70">
                  <FeatherIcon name="user" class="h-8 w-8" />
                </div>
              </template>

              <!-- Content -->
              <div
                class="relative px-4 pt-3 text-center"
                :class="{ 'pl-[38%] text-left': form.image_position === 'Left', 'pr-[38%] text-left': form.image_position === 'Right', 'pt-16 text-white': form.image_position === 'Cover' }"
              >
                <p class="text-[8px] uppercase tracking-[0.2em] mb-1" :style="{ color: form.image_position === 'Cover' ? '#e9c46a' : form.accent_color }">
                  You are cordially invited
                </p>
                <p class="font-display text-base leading-tight mb-2" :style="{ color: form.image_position === 'Cover' ? '#fff' : form.primary_color }">
                  John Doe
                </p>
                <div class="w-10 border-t mx-auto mb-2" :class="{ 'mx-0': form.image_position === 'Left' || form.image_position === 'Right' }" :style="{ borderColor: form.accent_color }"></div>
                <p class="text-[9px] leading-relaxed text-gray-600" :class="{ 'text-gray-200': form.image_position === 'Cover' }">
                  {{ previewMessage }}
                </p>
                <p class="text-[8px] mt-2 text-gray-500" :class="{ 'text-gray-200': form.image_position === 'Cover' }">
                  Sat 14 Mar 2026 · 10:00 AM · Venue
                </p>
              </div>

              <!-- QR placeholder -->
              <div
                class="absolute w-14 bg-white/95 border rounded-sm text-center py-1.5 shadow-sm"
                :style="{ borderColor: form.accent_color }"
                :class="qrPreviewClass"
              >
                <div class="w-9 h-9 mx-auto grid place-items-center" :style="{ background: form.accent_color, color: '#fff' }">
                  <FeatherIcon name="grid" class="h-4 w-4" />
                </div>
                <p class="text-[6px] text-gray-500 mt-0.5">QR · ABC12345</p>
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button variant="ghost" @click="showDialog = false">Cancel</Button>
        <Button variant="solid" :loading="saving" @click="saveTemplate">
          {{ editing ? __('Save Changes') : __('Create Template') }}
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FeatherIcon, Button, Dialog, FormControl } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import { useNotifications } from '@/composables/notifications'

const { showToast } = useNotifications()

const loading = ref(true)
const saving = ref(false)
const templates = ref([])
const showDialog = ref(false)
const editing = ref(null)

const layoutOptions = [
  { label: __('Classic'), value: 'Classic' },
  { label: __('Elegant'), value: 'Elegant' },
  { label: __('Modern'), value: 'Modern' },
  { label: __('Minimal'), value: 'Minimal' },
]

const imagePositionOptions = [
  { label: __('Top'), value: 'Top' },
  { label: __('Left'), value: 'Left' },
  { label: __('Right'), value: 'Right' },
  { label: __('Cover'), value: 'Cover' },
]

const qrPositionOptions = [
  { label: __('Bottom Right'), value: 'Bottom Right' },
  { label: __('Bottom Left'), value: 'Bottom Left' },
  { label: __('Top Right'), value: 'Top Right' },
  { label: __('Side Right'), value: 'Side Right' },
]

const emptyForm = () => ({
  template_name: '',
  title: '',
  layout: 'Classic',
  primary_color: '#8F3B1C',
  accent_color: '#C9A227',
  image_position: 'Top',
  qr_position: 'Bottom Right',
  invitation_message: 'Together with their families, {guest_name} is cordially invited to {event_name}.',
  enabled: 1,
  is_default: 0,
})

const form = ref(emptyForm())

const previewMessage = computed(() => {
  const msg = form.value.invitation_message || ''
  return msg.replace('{guest_name}', 'John Doe').replace('{event_name}', "John & Mary's Wedding").slice(0, 90)
})

const qrPreviewClass = computed(() => {
  const map = {
    'Bottom Right': 'bottom-1.5 right-1.5',
    'Bottom Left': 'bottom-1.5 left-1.5',
    'Top Right': 'top-1.5 right-1.5',
    'Side Right': 'right-1 top-1/2 -translate-y-1/2',
  }
  return map[form.value.qr_position] || 'bottom-1.5 right-1.5'
})

onMounted(loadTemplates)

async function loadTemplates() {
  loading.value = true
  try {
    const data = await frappeRequest({ url: 'invite.api.template.get_list' })
    templates.value = data.templates || []
  } catch (e) {
    console.error('Failed to load templates:', e)
    showToast('Failed to load templates', 'error')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(t) {
  editing.value = t
  form.value = {
    template_name: t.template_name || '',
    title: t.title || '',
    layout: t.layout || 'Classic',
    primary_color: t.primary_color || '#8F3B1C',
    accent_color: t.accent_color || '#C9A227',
    image_position: t.image_position || 'Top',
    qr_position: t.qr_position || 'Bottom Right',
    invitation_message: t.invitation_message || '',
    enabled: t.enabled ? 1 : 0,
    is_default: t.is_default ? 1 : 0,
  }
  showDialog.value = true
}

async function saveTemplate() {
  if (!form.value.template_name?.trim() || !form.value.title?.trim()) {
    showToast('Template name and title are required')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await frappeRequest({
        url: 'invite.api.template.update',
        params: { template: editing.value.name, data: JSON.stringify(form.value) },
      })
    } else {
      await frappeRequest({
        url: 'invite.api.template.create',
        params: { data: JSON.stringify(form.value) },
      })
    }
    showDialog.value = false
    await loadTemplates()
    showToast(editing.value ? 'Template updated' : 'Template created', 'success')
  } catch (e) {
    console.error('Failed to save template:', e)
    showToast(e.messages?.[0] || 'Failed to save template', 'error')
  } finally {
    saving.value = false
  }
}

async function removeTemplate(t) {
  if (!confirm(`Delete template "${t.title}"?`)) return
  try {
    await frappeRequest({ url: 'invite.api.template.delete', params: { template: t.name } })
    await loadTemplates()
    showToast('Template deleted', 'success')
  } catch (e) {
    console.error('Failed to delete template:', e)
    showToast(e.messages?.[0] || 'Failed to delete template', 'error')
  }
}
</script>