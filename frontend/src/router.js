import { createRouter, createWebHistory } from 'vue-router'
import { sessionStore } from '@/stores/session'

const routes = [
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
    path: '/events/:eventId/contributions',
    name: 'Contributions',
    component: () => import('@/pages/Contributions.vue'),
    props: true,
  },
  {
    path: '/events/:eventId/checkin',
    name: 'CheckIn',
    component: () => import('@/pages/CheckIn.vue'),
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
    path: '/committee',
    name: 'CommitteeMembers',
    component: () => import('@/pages/CommitteeMembers.vue'),
  },
  {
    path: '/settings',
    name: 'AppSettings',
    component: () => import('@/pages/AppSettings.vue'),
  },
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

router.beforeEach(async (to, from, next) => {
  const { isLoggedIn } = sessionStore()

  if (to.name === 'Home' && isLoggedIn) {
    next({ name: 'Dashboard' })
  } else if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/invite'
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else {
    next()
  }
})

export default router
