import { useState, useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useParams, useLocation } from 'react-router-dom'
import { MicrophoneIcon, StopIcon, XMarkIcon } from '@heroicons/react/24/solid'
import useVoiceRecorder from '../../hooks/useVoiceRecorder'
import useSpeechRecognition from '../../hooks/useSpeechRecognition'
import voiceService from '../../services/voiceService'
import {
  startRecording as startRecordingAction,
  stopRecording as stopRecordingAction,
  uploadStart,
  uploadSuccess,
  uploadFailure,
} from '../../store/slices/voiceSlice'
import {
  openConfirmationDialog,
  showNotification,
} from '../../store/slices/uiSlice'

const FloatingVoiceButton = () => {
  const { classNum, section, rollNumber, subjectId } = useParams() // Get current context from URL
  const location = useLocation() // Get current page path
  const dispatch = useDispatch()
  const [isExpanded, setIsExpanded] = useState(false)
  const { isRecording: isRecordingState, isProcessing, transcription: uploadedTranscription } = useSelector(
    (state) => state.voice
  )
  const userRole = useSelector((state) => state.auth.user?.role)

  const { isRecording, audioBlob, error: recorderError, startRecording, stopRecording, reset } =
    useVoiceRecorder()

  const {
    isListening,
    transcript: liveTranscript,
    error: recognitionError,
    startListening,
    stopListening,
    resetTranscript,
    isSupported
  } = useSpeechRecognition()

  const error = recorderError || recognitionError

  // Use ref to always get latest transcript (avoids stale closure issue)
  const transcriptRef = useRef(liveTranscript)
  useEffect(() => {
    transcriptRef.current = liveTranscript
  }, [liveTranscript])

  // Handle audio blob upload
  useEffect(() => {
    // Only upload if we have a valid audio blob with size > 0
    if (audioBlob && audioBlob.size > 0 && !isProcessing) {
      // Add a small delay to allow Web Speech API to finalize transcript
      const uploadTimer = setTimeout(() => {
        handleUpload()
      }, 500) // 500ms delay to let transcript finalize

      return () => clearTimeout(uploadTimer)
    }
  }, [audioBlob])

  const handleStartRecording = async () => {
    setIsExpanded(true)
    dispatch(startRecordingAction()) // This will clear previous transcription
    resetTranscript() // Clear previous live transcript

    // Start both audio recording and speech recognition
    await startRecording()
    if (isSupported) {
      startListening()
    }
  }

  const handleStopRecording = () => {
    dispatch(stopRecordingAction())
    stopRecording()
    if (isSupported) {
      stopListening()
    }
  }

  const handleUpload = async () => {
    try {
      dispatch(uploadStart())

      // Pass page context (class/section/roll/subject/page path) if available
      const context = {}
      if (classNum && section) {
        context.classNum = classNum
        context.section = section
      }
      if (rollNumber) {
        context.rollNumber = rollNumber
      }
      if (subjectId) {
        context.subjectId = subjectId
      }
      // Send current page path so backend can disambiguate (e.g. "go to reports" from fee page)
      context.currentPage = location.pathname

      // Use ref to get latest transcript (avoids stale closure)
      const currentTranscript = transcriptRef.current || ''
      console.log('[FloatingVoiceButton] Uploading with transcript:', currentTranscript)

      // Send live transcript from Web Speech API along with audio
      const result = await voiceService.uploadVoiceCommand(
        audioBlob,
        context,
        currentTranscript.trim()
      )

      console.log('[FloatingVoiceButton] Upload result:', result)
      console.log('[FloatingVoiceButton] Transcription:', result.transcription)
      console.log('[FloatingVoiceButton] Intent:', result.intent)
      console.log('[FloatingVoiceButton] Confirmation data:', result.confirmation_data)

      dispatch(uploadSuccess(result))
      dispatch(openConfirmationDialog())

      dispatch(
        showNotification({
          type: 'success',
          message: 'Voice command processed successfully',
        })
      )

      reset()
      resetTranscript()
    } catch (err) {
      console.error('Upload error:', err)

      let errorMessage = 'Failed to process voice command'

      // Safely extract error message from response
      if (err.response?.data) {
        const data = err.response.data
        // Handle different error response structures
        if (typeof data === 'string') {
          errorMessage = data
        } else if (data.error && typeof data.error === 'string') {
          errorMessage = data.error
        } else if (data.details && typeof data.details === 'string') {
          errorMessage = data.details
        } else if (data.message && typeof data.message === 'string') {
          errorMessage = data.message
        } else if (data.error && typeof data.error === 'object') {
          // Handle validation errors like {audio_file: ["This field is required"]}
          errorMessage = Object.values(data.error).flat().join(', ')
        } else {
          // Fallback: stringify the error object
          errorMessage = JSON.stringify(data)
        }
      } else if (err.message) {
        errorMessage = err.message
      }

      dispatch(uploadFailure(errorMessage))
      dispatch(
        showNotification({
          type: 'error',
          message: errorMessage,
        })
      )

      reset()
      resetTranscript()
    }
  }

  const handleClose = () => {
    setIsExpanded(false)
  }

  return (
    <>
      {/* Floating Action Button */}
      {!isExpanded && (
        <button
          onClick={handleStartRecording}
          disabled={isProcessing}
          className={`
            fixed bottom-6 right-6 z-50
            w-16 h-16 rounded-full shadow-2xl
            bg-gradient-to-r from-blue-500 to-purple-600
            hover:from-blue-600 hover:to-purple-700
            transition-all duration-300 transform hover:scale-110
            ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            flex items-center justify-center
            group
          `}
          title="Voice Command"
        >
          <MicrophoneIcon className="w-7 h-7 text-white group-hover:scale-110 transition-transform" />
        </button>
      )}

      {/* Expanded Voice Recorder Panel */}
      {isExpanded && (
        <div className="fixed bottom-6 right-6 z-50 bg-white rounded-2xl shadow-2xl w-96 max-w-[calc(100vw-3rem)]">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-t-2xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MicrophoneIcon className="w-5 h-5 text-white" />
              <h3 className="text-white font-semibold">Voice Command</h3>
            </div>
            <button
              onClick={handleClose}
              className="text-white hover:bg-white/20 rounded-full p-1 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            {/* Recording Button */}
            <div className="flex justify-center">
              <button
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                disabled={isProcessing}
                className={`
                  w-20 h-20 rounded-full transition-all duration-300
                  ${
                    isRecording
                      ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                      : 'bg-blue-500 hover:bg-blue-600'
                  }
                  ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  flex items-center justify-center shadow-lg
                `}
              >
                {isRecording ? (
                  <StopIcon className="w-8 h-8 text-white" />
                ) : (
                  <MicrophoneIcon className="w-8 h-8 text-white" />
                )}
              </button>
            </div>

            {/* Status */}
            <div className="text-center text-sm">
              {isProcessing && (
                <p className="text-blue-600 font-medium">Processing...</p>
              )}
              {isRecording && !isProcessing && (
                <p className="text-red-600 font-medium">Recording... Click to stop</p>
              )}
              {!isRecording && !isProcessing && (
                <p className="text-gray-600">Click to start recording</p>
              )}
            </div>

            {/* Transcription Display - Real-time */}
            {(isRecording || liveTranscript || uploadedTranscription) && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 min-h-[60px]">
                <p className="text-xs font-semibold text-gray-600 mb-1">
                  {isRecording ? '🎤 Listening...' : 'Transcription:'}
                </p>
                <p className="text-sm text-gray-800">
                  {isRecording ? (
                    liveTranscript ? (
                      <span className="font-medium">{liveTranscript}</span>
                    ) : (
                      <span className="text-gray-500 italic">Recording... (will transcribe after stop)</span>
                    )
                  ) : uploadedTranscription ? (
                    uploadedTranscription
                  ) : liveTranscript ? (
                    liveTranscript
                  ) : (
                    <span className="text-gray-400 italic">No transcription</span>
                  )}
                </p>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                {error}
              </div>
            )}

            {/* Quick Tips — role-aware */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs font-semibold text-blue-900 mb-1">Quick Examples:</p>
              <ul className="text-xs text-blue-800 space-y-1">
                {userRole === 'ACCOUNTANT' ? (
                  <>
                    <li>• "Collect 5000 from roll 12 cash"</li>
                    <li>• "Today's collection"</li>
                    <li>• "Show defaulters"</li>
                  </>
                ) : classNum && section ? (
                  <>
                    <li>• "Update marks roll 1 maths 95"</li>
                    <li>• "Mark all present"</li>
                    <li>• "Mark attendance"</li>
                  </>
                ) : (
                  <>
                    <li>• "Open marks for class 8B"</li>
                    <li>• "Open the attendance sheet"</li>
                    <li>• "Show marks for class 7C"</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default FloatingVoiceButton
