import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline'
import voiceService from '../../services/voiceService'
import {
  confirmStart,
  confirmSuccess,
  confirmFailure,
  rejectCommand,
} from '../../store/slices/voiceSlice'
import {
  closeConfirmationDialog,
  showNotification,
} from '../../store/slices/uiSlice'
import MarksPreview from '../marks/MarksPreview'
import QuestionMarksPreview from '../marks/QuestionMarksPreview'
import BatchQuestionMarksPreview from '../marks/BatchQuestionMarksPreview'
import AttendancePreview from '../attendance/AttendancePreview'
import StudentDetailsPreview from '../common/StudentDetailsPreview'
import NavigationPreview from '../common/NavigationPreview'

const ConfirmationDialog = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { showConfirmationDialog } = useSelector((state) => state.ui)
  const {
    currentCommand,
    transcription,
    intent,
    confirmationData,
    isProcessing,
  } = useSelector((state) => state.voice)

  if (!showConfirmationDialog || !confirmationData) {
    return null
  }

  // Debug logging
  console.log('[ConfirmationDialog] Rendering with:')
  console.log('[ConfirmationDialog] Transcription:', transcription)
  console.log('[ConfirmationDialog] Intent:', intent)
  console.log('[ConfirmationDialog] Confirmation data:', confirmationData)

  const handleConfirm = async () => {
    try {
      dispatch(confirmStart())

      const result = await voiceService.confirmCommand(currentCommand)

      console.log('Confirm result:', result)
      console.log('Navigation URL:', result?.result?.navigation?.url)

      dispatch(confirmSuccess(result))
      dispatch(closeConfirmationDialog())
      dispatch(
        showNotification({
          type: 'success',
          message: 'Command executed successfully',
        })
      )

      // Update localStorage for BATCH question marks
      if (intent === 'BATCH_UPDATE_QUESTION_MARKS') {
        console.log('=== UPDATING BATCH QUESTION MARKS IN LOCALSTORAGE ===')
        console.log('confirmationData:', confirmationData)
        console.log('result:', result)

        const { student, subject, updates } = confirmationData
        const totalMarks = result?.result?.total_marks

        if (student && subject && updates && updates.length > 0) {
          // Extract class and section
          const classMatch = student.class.match(/(\d+)(?:th|st|nd|rd)?([A-Z])/)

          if (classMatch) {
            const [, classNum, section] = classMatch
            const examType = 'UNIT_TEST'

            // Update question-wise marks for all updates
            const questionStorageKey = `questionMarks_${classNum}${section}_${examType}`
            const existingQuestionData = JSON.parse(localStorage.getItem(questionStorageKey) || '{}')

            if (!existingQuestionData[student.roll_number]) {
              existingQuestionData[student.roll_number] = {}
            }

            // Map subject name to ID
            const subjectMap = {
              'Mathematics': 1,
              'Hindi': 2,
              'English': 3,
              'Science': 4,
              'Social Studies': 5
            }
            const subjectId = subjectMap[subject.name]

            if (subjectId) {
              if (!existingQuestionData[student.roll_number][subjectId]) {
                existingQuestionData[student.roll_number][subjectId] = { questions: {} }
              }

              if (!existingQuestionData[student.roll_number][subjectId].questions) {
                existingQuestionData[student.roll_number][subjectId].questions = {}
              }

              // Apply all updates
              updates.forEach(update => {
                existingQuestionData[student.roll_number][subjectId].questions[update.question_number] = {
                  maxMarks: update.max_marks,
                  marksObtained: update.marks_obtained
                }
              })

              existingQuestionData[student.roll_number][subjectId].total = totalMarks

              localStorage.setItem(questionStorageKey, JSON.stringify(existingQuestionData))
              console.log('Batch question marks updated in localStorage')

              // Also update main marks with total
              if (totalMarks !== undefined) {
                const marksStorageKey = `marks_${classNum}${section}_${examType}`
                const existingMarks = JSON.parse(localStorage.getItem(marksStorageKey) || '{}')

                if (!existingMarks[student.roll_number]) {
                  existingMarks[student.roll_number] = {}
                }
                existingMarks[student.roll_number][subjectId] = totalMarks

                localStorage.setItem(marksStorageKey, JSON.stringify(existingMarks))

                // Dispatch storage event
                window.dispatchEvent(new StorageEvent('storage', {
                  key: marksStorageKey,
                  newValue: JSON.stringify(existingMarks),
                  url: window.location.href
                }))
                console.log('Subject total updated in localStorage from batch')
              }
            }
          }
        }
      }

      // Update localStorage for question marks if it's a question marks update command
      if (intent === 'UPDATE_QUESTION_MARKS') {
        console.log('=== UPDATING QUESTION MARKS IN LOCALSTORAGE ===')
        console.log('confirmationData:', confirmationData)
        console.log('result:', result)

        const { student, subject, question } = confirmationData
        const marksObtained = result?.result?.marks_obtained
        const totalMarks = result?.result?.total_marks

        if (student && subject && question && marksObtained !== undefined) {
          // Extract class and section
          const classMatch = student.class.match(/(\d+)(?:th|st|nd|rd)?([A-Z])/)

          if (classMatch) {
            const [, classNum, section] = classMatch
            const examType = 'UNIT_TEST'

            // Update question-wise marks
            const questionStorageKey = `questionMarks_${classNum}${section}_${examType}`
            const existingQuestionData = JSON.parse(localStorage.getItem(questionStorageKey) || '{}')

            if (!existingQuestionData[student.roll_number]) {
              existingQuestionData[student.roll_number] = {}
            }

            // Map subject name to ID
            const subjectMap = {
              'Mathematics': 1,
              'Hindi': 2,
              'English': 3,
              'Science': 4,
              'Social Studies': 5
            }
            const subjectId = subjectMap[subject.name]

            if (subjectId) {
              if (!existingQuestionData[student.roll_number][subjectId]) {
                existingQuestionData[student.roll_number][subjectId] = { questions: {} }
              }

              if (!existingQuestionData[student.roll_number][subjectId].questions) {
                existingQuestionData[student.roll_number][subjectId].questions = {}
              }

              existingQuestionData[student.roll_number][subjectId].questions[question.number] = {
                maxMarks: question.max_marks,
                marksObtained: marksObtained
              }

              existingQuestionData[student.roll_number][subjectId].total = totalMarks

              localStorage.setItem(questionStorageKey, JSON.stringify(existingQuestionData))
              console.log('Question marks updated in localStorage')

              // Also update main marks with total
              if (totalMarks !== undefined) {
                const marksStorageKey = `marks_${classNum}${section}_${examType}`
                const existingMarks = JSON.parse(localStorage.getItem(marksStorageKey) || '{}')

                if (!existingMarks[student.roll_number]) {
                  existingMarks[student.roll_number] = {}
                }
                existingMarks[student.roll_number][subjectId] = totalMarks

                localStorage.setItem(marksStorageKey, JSON.stringify(existingMarks))

                // Dispatch storage event
                window.dispatchEvent(new StorageEvent('storage', {
                  key: marksStorageKey,
                  newValue: JSON.stringify(existingMarks),
                  url: window.location.href
                }))
                console.log('Subject total updated in localStorage')
              }
            }
          }
        }
      }

      // Update localStorage for marks if it's a marks update command
      if (intent === 'UPDATE_MARKS' || intent === 'ENTER_MARKS') {
        console.log('=== UPDATING MARKS IN LOCALSTORAGE ===')
        console.log('confirmationData:', confirmationData)

        // Extract class, section, roll number, and marks from confirmationData
        const { student, marks_table } = confirmationData

        console.log('student:', student)
        console.log('marks_table:', marks_table)

        if (student && marks_table) {
          // Extract class and section from student.class (e.g., "5thB" -> class=5, section=B)
          const classMatch = student.class.match(/(\d+)(?:th|st|nd|rd)?([A-Z])/)
          console.log('classMatch:', classMatch)

          if (classMatch) {
            const [, classNum, section] = classMatch
            const examType = 'UNIT_TEST' // Default exam type
            const storageKey = `marks_${classNum}${section}_${examType}`

            console.log('storageKey:', storageKey)

            // Get existing marks from localStorage
            const existingMarks = JSON.parse(localStorage.getItem(storageKey) || '{}')
            console.log('existingMarks BEFORE update:', JSON.stringify(existingMarks))

            // CRITICAL FIX: Use roll_number as key (MarksSheetPage uses rollNumber which equals roll_number)
            const studentKey = student.roll_number

            // Update marks for this student
            if (!existingMarks[studentKey]) {
              existingMarks[studentKey] = {}
            }

            // Map subject names to IDs
            const subjectMap = {
              'Mathematics': 1,
              'Hindi': 2,
              'English': 3,
              'Science': 4,
              'Social Studies': 5
            }

            marks_table.forEach(mark => {
              const subjectId = subjectMap[mark.subject]
              console.log(`Updating student key ${studentKey}, subject ${mark.subject} (id: ${subjectId}) = ${mark.marks_obtained}`)
              if (subjectId) {
                existingMarks[studentKey][subjectId] = mark.marks_obtained
              }
            })

            console.log('existingMarks AFTER update:', JSON.stringify(existingMarks))

            // Save back to localStorage
            localStorage.setItem(storageKey, JSON.stringify(existingMarks))
            console.log('=== SAVED TO LOCALSTORAGE ===')

            // Dispatch storage event to notify other components
            window.dispatchEvent(new StorageEvent('storage', {
              key: storageKey,
              newValue: JSON.stringify(existingMarks),
              url: window.location.href
            }))
          } else {
            console.log('ERROR: Could not parse class from student.class:', student.class)
          }
        } else {
          console.log('ERROR: Missing student or marks_table in confirmationData')
        }
      }

      // Handle navigation if it's a navigation command
      if (result?.result?.navigation?.url) {
        console.log('Navigating to:', result.result.navigation.url)
        setTimeout(() => {
          navigate(result.result.navigation.url)
        }, 500) // Small delay to show success notification
      } else {
        console.log('No navigation URL found in result')

        // For marks/attendance commands, trigger a storage event to update the page
        if (intent === 'MARK_ATTENDANCE' || intent === 'UPDATE_MARKS' || intent === 'ENTER_MARKS') {
          console.log('Marks/attendance updated - page will reflect changes via localStorage')
          // The storage event was already dispatched above, no reload needed
          // The MarksSheetPage will reload from localStorage on next render
        }
      }
    } catch (err) {
      console.error('Confirm error:', err)

      let errorMessage = 'Failed to execute command'
      if (err.response?.data?.details) {
        errorMessage = err.response.data.details
      }

      dispatch(confirmFailure(errorMessage))
      dispatch(
        showNotification({
          type: 'error',
          message: errorMessage,
        })
      )
    }
  }

  const handleReject = async () => {
    try {
      await voiceService.rejectCommand(currentCommand)
      dispatch(rejectCommand())
      dispatch(closeConfirmationDialog())
      dispatch(
        showNotification({
          type: 'info',
          message: 'Command rejected',
        })
      )
    } catch (err) {
      console.error('Reject error:', err)
    }
  }

  const renderPreview = () => {
    switch (intent) {
      case 'CLARIFY':
        return (
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-yellow-800 font-medium mb-3">{confirmationData.message}</p>
              <div className="space-y-2">
                {confirmationData.examples?.map((example, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="text-yellow-600 font-bold">•</span>
                    <span className="text-gray-700 text-sm">{example}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      case 'BATCH_UPDATE_QUESTION_MARKS':
        return <BatchQuestionMarksPreview data={confirmationData} />
      case 'UPDATE_QUESTION_MARKS':
        return <QuestionMarksPreview data={confirmationData} />
      case 'ENTER_MARKS':
      case 'UPDATE_MARKS':
        return <MarksPreview data={confirmationData} />
      case 'MARK_ATTENDANCE':
        return <AttendancePreview data={confirmationData} />
      case 'VIEW_STUDENT':
        return <StudentDetailsPreview data={confirmationData} />
      case 'NAVIGATE_MARKS':
      case 'NAVIGATE_ATTENDANCE':
      case 'OPEN_MARKS_SHEET':
      case 'OPEN_ATTENDANCE_SHEET':
      case 'OPEN_QUESTION_SHEET':
        return <NavigationPreview data={confirmationData} />
      default:
        return <div>Unknown command type</div>
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
          <h2 className="text-xl font-bold">Confirm Voice Command</h2>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Transcription */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              You said:
            </h3>
            <p className="text-gray-900 italic">"{transcription}"</p>
          </div>

          {/* Intent */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-semibold text-gray-700">Action:</span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {intent?.replace('_', ' ')}
            </span>
          </div>

          {/* Preview based on intent */}
          <div className="border-t pt-4">{renderPreview()}</div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 rounded-b-lg flex justify-end space-x-3">
          <button
            onClick={handleReject}
            disabled={isProcessing}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <XMarkIcon className="w-5 h-5" />
            <span>{intent === 'CLARIFY' ? 'OK' : 'Cancel'}</span>
          </button>
          {intent !== 'CLARIFY' && (
            <button
              onClick={handleConfirm}
              disabled={isProcessing}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <CheckIcon className="w-5 h-5" />
            <span>{isProcessing ? 'Processing...' : 'Confirm'}</span>
          </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default ConfirmationDialog
