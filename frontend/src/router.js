import { createRouter, createWebHistory } from 'vue-router'
import { sessionStore } from '@/stores/session'
import { useRoleInfo } from '@/composables/roles'

// Public routes that don't require authentication
const publicRoutes = [
  {
    path: '/rsvp',
    name: 'PublicRSVP',
    component: () => import('@/pages/PublicRSVP.vue'),
  },
  {
    path: '/event/:eventName',
    name: 'PublicEvent',
    component: () => import('@/pages/PublicEvent.vue'),
    props: true,
  },
]

// Authenticated routes
const authRoutes = [
  {
    path: '/',
    name: 'Home',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/events',
    name: 'Events',
    component: () => import('@/pages/Events.vue'),
  },
  {
    path: '/events/:eventId',
    name: 'EventDetail',
    component: () => import('@/pages/EventDetail.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/guests',
    name: 'Guests',
    component: () => import('@/pages/Guests.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/invitations',
    name: 'Invitations',
    component: () => import('@/pages/Invitations.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/checkin',
    name: 'CheckIn',
    component: () => import('@/pages/CheckIn.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/audit-log',
    name: 'AuditLog',
    component: () => import('@/pages/AuditLog.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/reports',
    name: 'Reports',
    component: () => import('@/pages/Reports.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/settings',
    name: 'EventSettings',
    component: () => import('@/pages/EventSettings.vue'),
    props: true,
  },
  {
    path: '/frontdesk',
    name: 'Frontdesk',
    component: () => import('@/pages/Frontdesk.vue'),
  },
  {
    path: '/audit-log',
    name: 'GlobalAuditLog',
    component: () => import('@/pages/AuditLog.vue'),
  },
  {
    path: '/settings',
    name: 'AppSettings',
    component: () => import('@/pages/AppSettings.vue'),
  },
]

const routes = [
  ...publicRoutes,
  ...authRoutes,
  {
    path: '/:invalidpath',
    name: 'Invalid Page',
    component: () => import('@/pages/InvalidPage.vue'),
  },
]

let router = createRouter({
  history: createWebHistory('/invite'),
  routes,
})

// Public route names that don't require authentication
const publicRouteNames = publicRoutes.map(r => r.name)

const { getRoleInfo } = useRoleInfo()

router.beforeEach(async (to, from, next) => {
  const { isLoggedIn } = sessionStore()

  // Allow public routes without authentication
  if (publicRouteNames.includes(to.name)) {
    next()
    return
  }

  if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/invite'
    return
  }

  // Home redirect: check frontdesk-only role
  if (to.name === 'Home') {
    const roleInfo = await getRoleInfo()
    if (roleInfo.is_frontdesk_only) {
      next({ name: 'Frontdesk' })
    } else {
      next({ name: 'Dashboard' })
    }
    return
  }

  // Frontdesk-only users should only access Frontdesk and Audit Log pages
  if (to.name !== 'Frontdesk' && to.name !== 'GlobalAuditLog' && to.name !== 'Invalid Page') {
    const roleInfo = await getRoleInfo()
    if (roleInfo.is_frontdesk_only) {
      next({ name: 'Frontdesk' })
      return
    }
  }

  if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else {
    next()
  }
})

export default router
