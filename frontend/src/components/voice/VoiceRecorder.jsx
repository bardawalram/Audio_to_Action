import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid'
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

const VoiceRecorder = () => {
  const dispatch = useDispatch()
  const { isRecording: isRecordingState, isProcessing } = useSelector(
    (state) => state.voice
  )
  const userRole = useSelector((state) => state.auth.user?.role)

  const { isRecording, audioBlob, error: recorderError, startRecording, stopRecording, reset } =
    useVoiceRecorder()

  const {
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
    dispatch(startRecordingAction())
    resetTranscript()
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

      // Use ref to get latest transcript (avoids stale closure)
      const currentTranscript = transcriptRef.current || ''
      console.log('[VoiceRecorder] Uploading with transcript:', currentTranscript)

      // Pass empty context for main voice recorder (no page context) + live transcript
      const result = await voiceService.uploadVoiceCommand(
        audioBlob,
        {},
        currentTranscript.trim()
      )

      dispatch(uploadSuccess(result))
      dispatch(openConfirmationDialog())

      // Show success notification
      dispatch(
        showNotification({
          type: 'success',
          message: 'Voice command processed successfully',
        })
      )

      // Reset recorder
      reset()
      resetTranscript()
    } catch (err) {
      console.error('Upload error:', err)

      let errorMessage = 'Failed to process voice command'
      if (err.response?.data?.error) {
        errorMessage = err.response.data.error
      } else if (err.response?.data?.details) {
        errorMessage = err.response.data.details
      }

      dispatch(uploadFailure(errorMessage))
      dispatch(
        showNotification({
          type: 'error',
          message: errorMessage,
        })
      )

      // Reset recorder
      reset()
      resetTranscript()
    }
  }

  const { transcription: uploadedTranscription } = useSelector((state) => state.voice)

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full">
        <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
          Voice Command
        </h2>

        <div className="flex flex-col items-center space-y-6">
          {/* Recording button */}
          <button
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            disabled={isProcessing}
            className={`
              relative w-32 h-32 rounded-full transition-all duration-300
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
              <StopIcon className="w-12 h-12 text-white" />
            ) : (
              <MicrophoneIcon className="w-12 h-12 text-white" />
            )}
          </button>

          {/* Status text */}
          <div className="text-center">
            {isProcessing && (
              <p className="text-blue-600 font-medium">Processing voice command...</p>
            )}
            {isRecording && !isProcessing && (
              <p className="text-red-600 font-medium">Recording... Click to stop</p>
            )}
            {!isRecording && !isProcessing && (
              <p className="text-gray-600">Click to start recording</p>
            )}
          </div>

          {/* Real-time Transcription Display */}
          {(isRecording || liveTranscript || uploadedTranscription) && (
            <div className="w-full bg-gray-50 border-2 border-gray-300 rounded-lg p-4 min-h-[100px]">
              <h3 className="font-semibold text-gray-700 mb-2 flex items-center">
                <MicrophoneIcon className="w-5 h-5 mr-2 text-blue-600" />
                {isRecording ? '🎤 Listening...' : 'Transcription:'}
              </h3>
              <p className="text-lg text-gray-800">
                {isRecording ? (
                  liveTranscript ? (
                    <span className="font-medium">{liveTranscript}</span>
                  ) : (
                    <span className="text-gray-500 italic">Recording... (transcription will appear after processing)</span>
                  )
                ) : uploadedTranscription ? (
                  uploadedTranscription
                ) : liveTranscript ? (
                  liveTranscript
                ) : (
                  <span className="text-gray-400 italic">No transcription yet</span>
                )}
              </p>
            </div>
          )}

          {/* Error display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded w-full">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Instructions — role-aware */}
          <div className="bg-blue-50 border border-blue-200 rounded p-4 w-full">
            <h3 className="font-semibold text-blue-900 mb-2">Example Commands:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              {userRole === 'ACCOUNTANT' ? (
                <>
                  <li>• "Open fee collections" or "Open fee reports"</li>
                  <li>• "Collect 5000 from roll 12 class 6A cash"</li>
                  <li>• "Today's collection" or "Show defaulters"</li>
                  <li>• "Show fee details of student 12345"</li>
                </>
              ) : (
                <>
                  <li>• "Open marks" or "Open attendance"</li>
                  <li>• "Open marks for class 8B"</li>
                  <li>• "Enter marks for roll number 1, class 8B. Maths 85, Hindi 78"</li>
                  <li>• "Mark attendance for class 8B"</li>
                  <li>• "Show details of student roll number 5, class 8B"</li>
                </>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VoiceRecorder
