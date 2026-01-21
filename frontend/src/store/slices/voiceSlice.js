import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  currentCommand: null,
  transcription: null,
  intent: null,
  confirmationData: null,
  isProcessing: false,
  isRecording: false,
  error: null,
  commandHistory: [],
}

const voiceSlice = createSlice({
  name: 'voice',
  initialState,
  reducers: {
    startRecording: (state) => {
      state.isRecording = true
      state.error = null
      state.transcription = null // Clear previous transcription
    },
    stopRecording: (state) => {
      state.isRecording = false
    },
    uploadStart: (state) => {
      state.isProcessing = true
      state.error = null
    },
    uploadSuccess: (state, action) => {
      state.isProcessing = false
      state.currentCommand = action.payload.command_id
      state.transcription = action.payload.transcription
      state.intent = action.payload.intent
      state.confirmationData = action.payload.confirmation_data
    },
    uploadFailure: (state, action) => {
      state.isProcessing = false
      state.error = action.payload
    },
    confirmStart: (state) => {
      state.isProcessing = true
      state.error = null
    },
    confirmSuccess: (state, action) => {
      state.isProcessing = false
      state.currentCommand = null
      state.transcription = null
      state.intent = null
      state.confirmationData = null
    },
    confirmFailure: (state, action) => {
      state.isProcessing = false
      state.error = action.payload
    },
    rejectCommand: (state) => {
      state.currentCommand = null
      state.transcription = null
      state.intent = null
      state.confirmationData = null
      state.error = null
    },
    clearError: (state) => {
      state.error = null
    },
    setCommandHistory: (state, action) => {
      state.commandHistory = action.payload
    },
  },
})

export const {
  startRecording,
  stopRecording,
  uploadStart,
  uploadSuccess,
  uploadFailure,
  confirmStart,
  confirmSuccess,
  confirmFailure,
  rejectCommand,
  clearError,
  setCommandHistory,
} = voiceSlice.actions

export default voiceSlice.reducer
