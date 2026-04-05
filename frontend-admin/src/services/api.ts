import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token（兼容直接存储和 zustand persist）
    let token = localStorage.getItem('token')

    // 如果没有直接存储的token，尝试从 zustand persist 读取
    if (!token) {
      const authStorage = localStorage.getItem('auth-storage')
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage)
          token = parsed.state?.token
        } catch (e) {
          console.error('Failed to parse auth-storage:', e)
        }
      }
    }

    console.log('[API Request]', config.url, 'Token:', token ? '存在' : '不存在')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // 如果是 401 错误且不是刷新 token 的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      let refreshToken = localStorage.getItem('refreshToken')

      // 如果没有直接存储的refreshToken，尝试从 zustand persist 读取
      if (!refreshToken) {
        const authStorage = localStorage.getItem('auth-storage')
        if (authStorage) {
          try {
            const parsed = JSON.parse(authStorage)
            refreshToken = parsed.state?.refreshToken
          } catch (e) {
            console.error('Failed to parse auth-storage for refresh token:', e)
          }
        }
      }

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data
          localStorage.setItem('token', access_token)

          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // 刷新失败，清除登录状态
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          // 清除 zustand persist 存储
          localStorage.removeItem('auth-storage')
          // 触发 storage 事件通知其他标签页
          window.dispatchEvent(new StorageEvent('storage', { key: 'auth-storage' }))
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // 没有 refresh token，直接跳转到登录页
        console.error('No refresh token, redirecting to login')
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        // 清除 zustand persist 存储
        localStorage.removeItem('auth-storage')
        // 触发 storage 事件通知其他标签页
        window.dispatchEvent(new StorageEvent('storage', { key: 'auth-storage' }))
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default api