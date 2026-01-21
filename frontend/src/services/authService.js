import api from './api'

const authService = {
  /**
   * Login user
   */
  login: async (username, password) => {
    const response = await api.post('/auth/login/', {
      username,
      password,
    })
    return response.data
  },

  /**
   * Logout user
   */
  logout: async () => {
    // Could call backend logout endpoint if implemented
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  },

  /**
   * Get current user info
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/me/')
    return response.data
  },

  /**
   * Refresh access token
   */
  refreshToken: async (refreshToken) => {
    const response = await api.post('/auth/token/refresh/', {
      refresh: refreshToken,
    })
    return response.data
  },
}

export default authService
