import api from './api'

const feeService = {
  getDashboard: () => api.get('/fees/dashboard/'),

  getFeeStructures: (classId) => {
    const params = classId ? { class_id: classId } : {}
    return api.get('/fees/structures/', { params })
  },

  getStudentFeeStatus: (classNum, section) =>
    api.get(`/fees/students/${classNum}/${section}/`),

  getStudentFeeDetails: (studentId) =>
    api.get(`/fees/student/${studentId}/details/`),

  collectFee: (data) => api.post('/fees/collect/', data),

  getPaymentHistory: (filters = {}) =>
    api.get('/fees/payments/', { params: filters }),

  getTodayCollection: () => api.get('/fees/reports/today/'),

  getDefaulters: (classNum) => {
    const params = classNum ? { class_num: classNum } : {}
    return api.get('/fees/reports/defaulters/', { params })
  },

  getClassWiseReport: () => api.get('/fees/reports/class-wise/'),

  getMonthlyReport: (months = 6) =>
    api.get('/fees/reports/monthly/', { params: { months } }),
}

export default feeService
