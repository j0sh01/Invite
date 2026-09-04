import { ref, computed } from 'vue'

export const showAboutModal = ref(false)
export const showSettings = ref(false)
export const showHelpModal = ref(false)

// Reactive viewport width so the app shell can adapt live when the window is
// resized or a device is rotated, without needing a page reload.
export const viewportWidth = ref(
	typeof window !== 'undefined' ? window.innerWidth : 1024,
)

export function initViewportListener() {
	const onResize = () => {
		viewportWidth.value = window.innerWidth
	}
	window.addEventListener('resize', onResize)
	window.addEventListener('orientationchange', onResize)
	return () => {
		window.removeEventListener('resize', onResize)
		window.removeEventListener('orientationchange', onResize)
	}
}

// < 768px: phones get the mobile shell (hamburger drawer sidebar)
export const isMobileView = computed(() => viewportWidth.value < 768)

// 768-1023px: desktop shell on tablets/small windows, but the sidebar starts
// collapsed so page content keeps enough room.
export const isCompactDesktop = computed(
	() => viewportWidth.value >= 768 && viewportWidth.value < 1024,
)

export const mobileSidebarOpened = ref(false)

export function toggleMobileSidebar() {
	mobileSidebarOpened.value = !mobileSidebarOpened.value
}
