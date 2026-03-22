import { defineStore } from 'pinia'
import { api } from '../api/client'

interface AuthState {
  username: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    username: localStorage.getItem('username')
  }),

  actions: {
    async checkAuth() {
      if (!this.username) return
      try {
        const resp = await fetch('/api/auth/me', { credentials: 'include' })
        if (resp.ok) {
          const data = await resp.json()
          this.username = data.username
          localStorage.setItem('username', this.username!)
        } else {
          this.username = null
          localStorage.removeItem('username')
        }
      } catch {
        this.username = null
        localStorage.removeItem('username')
      }
    },

    async login(username: string, password: string) {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await api.post('/auth/login', formData)
      this.username = response.data.username
      localStorage.setItem('username', this.username!)
    },

    async logout() {
      await api.post('/auth/logout')
      this.username = null
      localStorage.removeItem('username')
    }
  }
})
