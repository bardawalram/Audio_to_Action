import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  user: null,
  token: localStorage.getItem('token'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!localStorage.getItem('token'),
  loading: false,
  error: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true
      state.error = null
    },
    loginSuccess: (state, action) => {
      state.loading = false
      state.isAuthenticated = true
      state.token = action.payload.access
      state.refreshToken = action.payload.refresh
      state.user = action.payload.user
      localStorage.setItem('token', action.payload.access)
      localStorage.setItem('refreshToken', action.payload.refresh)
    },
    loginFailure: (state, action) => {
      state.loading = false
      state.error = action.payload
      state.isAuthenticated = false
    },
    logout: (state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.loading = false
      state.error = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
    },
    setUser: (state, action) => {
      state.user = action.payload
    },
    updateToken: (state, action) => {
      state.token = action.payload
      localStorage.setItem('token', action.payload)
    },
  },
})

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  setUser,
  updateToken
} = authSlice.actions

export default authSlice.reducer
