<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0 z-40">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="relative z-10 flex h-full w-[270px] flex-col justify-between border-r border-hairline bg-paper"
        >
          <!-- User menu (apps / desk / settings / logout) on top -->
          <div class="p-3">
            <UserDropdown />
          </div>

          <!-- Navigation -->
          <div class="flex-1 overflow-y-auto px-3 pb-3">
            <template v-for="group in navGroups" :key="group.label">
              <p
                v-if="group.items.length"
                class="px-3 pb-1.5 pt-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-400"
              >
                {{ group.label }}
              </p>
              <div class="flex flex-col gap-0.5">
                <SidebarLink
                  v-for="link in group.items"
                  :key="link.to"
                  :icon="link.icon"
                  :label="__(link.label)"
                  :to="link.to"
                  @click="sidebarOpened = false"
                />
              </div>
            </template>
          </div>

        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/40" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { TransitionRoot, TransitionChild, Dialog } from '@headlessui/vue'
import SidebarLink from '@/components/SidebarLink.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
import { useRoleInfo } from '@/composables/roles'

const { getRoleInfo } = useRoleInfo()
const isFrontdeskOnly = ref(false)

onMounted(async () => {
  const info = await getRoleInfo()
  isFrontdeskOnly.value = info.is_frontdesk_only
})

const allGroups = [
  {
    label: 'Workspace',
    items: [
      { label: 'Dashboard', icon: 'home', to: 'Dashboard', frontdeskOnly: false },
      { label: 'Events', icon: 'calendar', to: 'Events', frontdeskOnly: false },
    ],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Frontdesk', icon: 'camera', to: 'Frontdesk', frontdeskOnly: true },
      {
        label: 'Audit Log',
        icon: 'clipboard',
        to: 'GlobalAuditLog',
        frontdeskOnly: null,
      },
      { label: 'Templates', icon: 'layout', to: 'Templates', frontdeskOnly: false },
      { label: 'Settings', icon: 'settings', to: 'AppSettings', frontdeskOnly: false },
    ],
  },
]

const navGroups = computed(() => {
  return allGroups
    .map((group) => ({
      label: group.label,
      items: group.items.filter((item) => {
        if (item.frontdeskOnly === null) return true
        if (item.frontdeskOnly) return isFrontdeskOnly.value
        return !isFrontdeskOnly.value
      }),
    }))
    .filter((group) => group.items.length)
})
</script>
