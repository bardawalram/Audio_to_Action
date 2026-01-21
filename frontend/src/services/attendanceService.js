import api from './api'

const attendanceService = {
  /**
   * Get attendance for a class section
   */
  getAttendance: async (classSectionId, date) => {
    const response = await api.get(`/attendance/sessions/`, {
      params: { class_section: classSectionId, date }
    })
    return response.data
  },

  /**
   * Mark attendance for a class
   */
  markAttendance: async (classSectionId, date, attendanceData) => {
    const response = await api.post('/attendance/mark/', {
      class_section: classSectionId,
      date,
      records: attendanceData
    })
    return response.data
  },

  /**
   * Update attendance record
   */
  updateAttendance: async (recordId, status) => {
    const response = await api.patch(`/attendance/records/${recordId}/`, {
      status
    })
    return response.data
  },
}

export default attendanceService
