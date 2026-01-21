import api from './api'

const voiceService = {
  /**
   * Upload voice command audio file
   */
  uploadVoiceCommand: async (audioBlob, context = {}, liveTranscript = null) => {
    const formData = new FormData()
    formData.append('audio_file', audioBlob, 'voice_command.webm')

    // Add live transcript if available (from Web Speech API)
    if (liveTranscript) {
      formData.append('live_transcript', liveTranscript)
    }

    // Add context information if available
    if (context.classNum) {
      formData.append('context_class', context.classNum)
    }
    if (context.section) {
      formData.append('context_section', context.section)
    }
    if (context.rollNumber) {
      formData.append('context_roll_number', context.rollNumber)
    }
    if (context.subjectId) {
      formData.append('context_subject_id', context.subjectId)
    }

    try {
      // CRITICAL: Delete Content-Type header to let browser set multipart/form-data with boundary
      const response = await api.post('/voice/upload/', formData, {
        headers: {
          'Content-Type': undefined, // Let browser set it with boundary
        },
      })
      return response.data
    } catch (error) {
      // Extract readable error message from response
      const errorMessage = error.response?.data?.error
        || error.response?.data?.message
        || error.message
        || 'Voice upload failed'

      console.error('[Voice Upload Error]:', errorMessage)
      throw new Error(errorMessage)
    }
  },

  /**
   * Confirm and execute voice command
   */
  confirmCommand: async (commandId) => {
    const response = await api.post(`/voice/commands/${commandId}/confirm/`)
    return response.data
  },

  /**
   * Reject voice command
   */
  rejectCommand: async (commandId) => {
    const response = await api.post(`/voice/commands/${commandId}/reject/`)
    return response.data
  },

  /**
   * Get command history
   */
  getCommandHistory: async () => {
    const response = await api.get('/voice/commands/')
    return response.data
  },

  /**
   * Get command details
   */
  getCommand: async (commandId) => {
    const response = await api.get(`/voice/commands/${commandId}/`)
    return response.data
  },
}

export default voiceService
