import { createRouter, createWebHistory } from 'vue-router'
import { ref } from 'vue'
import LoginPage from '@/views/LoginPage.vue'
import AppPage from '@/views/AppPage.vue'

const isAuthenticated = ref(false);
const userId = ref('');

function clearAuth(router) {
  isAuthenticated.value = false;
  localStorage.removeItem('isAuthenticated');
  router.push('/login');
}

const routes = [
  { path: '/login', component: LoginPage },
  { path: '/', component: AppPage, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation Guard
router.beforeEach(async (to, from, next) => {
  console.log(`Navigating from: ${from.path} to: ${to.path}`);
  console.log(`isAuthenticated: ${isAuthenticated.value}`);

  if (to.path === '/login') {
    // If going to the login page, allow it regardless of authentication status
    next();
  } else {
    // For all other routes, check authentication
    try {
      const res = await fetch('http://127.0.0.1:5000/check-session', {
        method: 'GET',
        credentials: 'include'
      });
      if (res.status === 401) {
        clearAuth(router);
        next('/login');
      } else if (res.ok) {
        isAuthenticated.value = true;
        next();
      } else {
        clearAuth(router);
        next('/login');
      }
    } catch (error) {
      console.error("Error checking session:", error);
      clearAuth(router);
      next('/login');
    }
  }
});

export { router, isAuthenticated, clearAuth, userId }
export default router
