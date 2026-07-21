import { ref, computed } from 'vue'

export const showAboutModal = ref(false)
export const showSettings = ref(false)
export const showHelpModal = ref(false)

export const isMobileView = computed(() => window.innerWidth < 768)
export const mobileSidebarOpened = ref(false)

export function toggleMobileSidebar() {
	mobileSidebarOpened.value = !mobileSidebarOpened.value
}
