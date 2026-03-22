import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Cameras',
    component: () => import('./views/Cameras.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recordings',
    name: 'Recordings',
    component: () => import('./views/Recordings.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.path === '/login') {
    next()
    return
  }
  
  if (to.meta.requiresAuth && !authStore.username) {
    next('/login')
  } else {
    next()
  }
})

export default router
