import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import voiceReducer from './slices/voiceSlice'
import uiReducer from './slices/uiSlice'
import feeReducer from './slices/feeSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    voice: voiceReducer,
    ui: uiReducer,
    fee: feeReducer,
  },
})

export default store
