import { createSlice } from '@reduxjs/toolkit'

const feeSlice = createSlice({
  name: 'fee',
  initialState: {
    dashboard: null,
    classFeeStatus: null,
    studentDetails: null,
    defaulters: null,
    todayCollection: null,
    classWiseReport: null,
    monthlyReport: null,
    paymentHistory: [],
    loading: false,
    error: null,
  },
  reducers: {
    setLoading: (state, action) => {
      state.loading = action.payload
    },
    setDashboard: (state, action) => {
      state.dashboard = action.payload
      state.loading = false
    },
    setClassFeeStatus: (state, action) => {
      state.classFeeStatus = action.payload
      state.loading = false
    },
    setStudentDetails: (state, action) => {
      state.studentDetails = action.payload
      state.loading = false
    },
    setDefaulters: (state, action) => {
      state.defaulters = action.payload
      state.loading = false
    },
    setTodayCollection: (state, action) => {
      state.todayCollection = action.payload
      state.loading = false
    },
    setClassWiseReport: (state, action) => {
      state.classWiseReport = action.payload
      state.loading = false
    },
    setMonthlyReport: (state, action) => {
      state.monthlyReport = action.payload
      state.loading = false
    },
    setPaymentHistory: (state, action) => {
      state.paymentHistory = action.payload
      state.loading = false
    },
    setError: (state, action) => {
      state.error = action.payload
      state.loading = false
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

export const {
  setLoading,
  setDashboard,
  setClassFeeStatus,
  setStudentDetails,
  setDefaulters,
  setTodayCollection,
  setClassWiseReport,
  setMonthlyReport,
  setPaymentHistory,
  setError,
  clearError,
} = feeSlice.actions

export default feeSlice.reducer
