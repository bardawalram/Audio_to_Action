import api from './api'

const marksService = {
  /**
   * Get marks for a student
   */
  getStudentMarks: async (studentId) => {
    const response = await api.get(`/marks/student/${studentId}/`)
    return response.data
  },

  /**
   * Get all subjects
   */
  getSubjects: async () => {
    const response = await api.get('/marks/subjects/')
    return response.data
  },

  /**
   * Get exam types
   */
  getExamTypes: async () => {
    const response = await api.get('/marks/exam-types/')
    return response.data
  },

  /**
   * Update marks
   */
  updateMarks: async (studentId, examTypeId, subjectId, marks) => {
    const response = await api.post('/marks/update/', {
      student: studentId,
      exam_type: examTypeId,
      subject: subjectId,
      marks_obtained: marks
    })
    return response.data
  },

  /**
   * Get marks for a class section
   */
  getClassMarks: async (classSectionId, examTypeId) => {
    const response = await api.get(`/marks/class/${classSectionId}/`, {
      params: { exam_type: examTypeId }
    })
    return response.data
  },
}

export default marksService
