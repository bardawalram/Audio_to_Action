import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  showConfirmationDialog: false,
  showVoiceRecorder: false,
  loading: false,
  notification: null,
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    openConfirmationDialog: (state) => {
      state.showConfirmationDialog = true
    },
    closeConfirmationDialog: (state) => {
      state.showConfirmationDialog = false
    },
    openVoiceRecorder: (state) => {
      state.showVoiceRecorder = true
    },
    closeVoiceRecorder: (state) => {
      state.showVoiceRecorder = false
    },
    setLoading: (state, action) => {
      state.loading = action.payload
    },
    showNotification: (state, action) => {
      state.notification = {
        type: action.payload.type, // 'success' | 'error' | 'info' | 'warning'
        message: action.payload.message,
      }
    },
    hideNotification: (state) => {
      state.notification = null
    },
  },
})

export const {
  openConfirmationDialog,
  closeConfirmationDialog,
  openVoiceRecorder,
  closeVoiceRecorder,
  setLoading,
  showNotification,
  hideNotification,
} = uiSlice.actions

export default uiSlice.reducer
