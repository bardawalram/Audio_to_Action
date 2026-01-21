import api from './api'

const academicsService = {
  /**
   * Get all classes with sections
   */
  getClassesWithSections: async () => {
    const response = await api.get('/academics/classes-with-sections/')
    return response.data
  },

  /**
   * Get students for a specific class section
   */
  getStudentsByClassSection: async (classId, sectionName) => {
    const response = await api.get(`/academics/students/?class=${classId}&section=${sectionName}`)
    return response.data
  },

  /**
   * Get student details
   */
  getStudentDetails: async (studentId) => {
    const response = await api.get(`/academics/students/${studentId}/`)
    return response.data
  },
}

export default academicsService
