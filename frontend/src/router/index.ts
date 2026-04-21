import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Submission from '../views/Submission.vue'
import Result from '../views/Result.vue'
import TeacherDashboard from '../views/TeacherDashboard.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: Login,
        },
        {
            path: '/',
            name: 'Dashboard',
            component: Dashboard,
            meta: { requiresAuth: true, roles: ['student'] },
        },
        {
            path: '/teacher',
            name: 'TeacherDashboard',
            component: TeacherDashboard,
            meta: { requiresAuth: true, roles: ['instructor', 'admin'] },
        },
        {
            path: '/submission',
            name: 'Submission',
            component: Submission,
            meta: { requiresAuth: true },
        },
        {
            path: '/result/:id',
            name: 'Result',
            component: Result,
            meta: { requiresAuth: true },
        },
    ],
})

router.beforeEach(async (to, _from, next) => {
    const authStore = useAuthStore()

    if (to.meta.requiresAuth && !authStore.token) {
        next('/login')
        return
    }

    if (to.meta.requiresAuth && authStore.token && !authStore.user) {
        await authStore.fetchUser()
    }

    if (to.path === '/login' && authStore.isAuthenticated && authStore.user) {
        next(authStore.getDefaultRouteByRole())
        return
    }

    const roles = to.meta.roles as string[] | undefined
    if (roles && authStore.user && !roles.includes(authStore.user.role)) {
        next(authStore.getDefaultRouteByRole())
        return
    }

    next()
})

export default router
