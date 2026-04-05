import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

interface User {
  id: string
  username: string
  email: string
  full_name?: string
  role?: {
    id: number
    name: string
    code: string
  }
  is_active: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          const formData = new FormData()
          formData.append('username', username)
          formData.append('password', password)

          const response = await api.post('/auth/login', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })

          const { access_token, refresh_token } = response.data
          localStorage.setItem('token', access_token)
          localStorage.setItem('refreshToken', refresh_token)

          // 获取用户信息
          const userResponse = await api.get('/auth/me', {
            headers: {
              Authorization: `Bearer ${access_token}`,
            },
          })

          set({
            user: userResponse.data,
            token: access_token,
            isAuthenticated: true,
          })

          return true
        } catch (error) {
          console.error('Login failed:', error)
          return false
        }
      },

      logout: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      checkAuth: () => {
        const token = localStorage.getItem('token')
        if (token) {
          // 验证 token 是否有效
          api.get('/auth/me', {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          })
            .then((response) => {
              set({
                user: response.data,
                token: token,
                isAuthenticated: true,
              })
            })
            .catch(() => {
              localStorage.removeItem('token')
              localStorage.removeItem('refreshToken')
              // 清除 zustand persist 存储
              localStorage.removeItem('auth-storage')
              // 重置状态
              set({
                user: null,
                token: null,
                isAuthenticated: false,
              })
              // 跳转到登录页
              window.location.href = '/login'
            })
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)