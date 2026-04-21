import { defineStore } from 'pinia'
import request from '../utils/request'


interface User {
    id: number
    email: string
    full_name?: string
    role: string
}

interface AuthState {
    token: string | null
    user: User | null
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthState => ({
        token: localStorage.getItem('token'),
        user: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
    },
    actions: {
        normalizeRole(role?: string) {
            if (!role) return ''
            const raw = String(role).trim()
            if (!raw) return ''
            if (raw.includes('.')) {
                return raw.split('.').pop()!.toLowerCase()
            }
            return raw.toLowerCase()
        },
        async login(username: string, password: string) {
            try {
                const formData = new URLSearchParams()
                formData.append('username', username.trim())
                formData.append('password', password)

                const response = await request.post('/login/access-token', formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                })
                const { access_token } = response.data

                this.token = access_token
                localStorage.setItem('token', access_token)
                await this.fetchUser()
                return !!this.user
            } catch (error) {
                return false
            }
        },
        async registerStudent(email: string, password: string, fullName?: string) {
            await request.post('/users/register-student', {
                email: email.trim().toLowerCase(),
                password,
                full_name: fullName?.trim() || null,
            })
        },
        async fetchUser() {
            try {
                const response = await request.get('/users/me')
                const user = response.data
                this.user = {
                    ...user,
                    role: this.normalizeRole(user.role),
                }
            } catch (error) {
                this.logout()
            }
        },
        getDefaultRouteByRole() {
            if (!this.user) return '/login'
            if (this.user.role === 'instructor' || this.user.role === 'admin') return '/teacher'
            return '/'
        },
        logout() {
            this.token = null
            this.user = null
            localStorage.removeItem('token')
            window.location.href = '/login'
        },
    },
})
