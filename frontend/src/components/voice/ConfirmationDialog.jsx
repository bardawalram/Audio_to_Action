import { useEffect, useState, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { XMarkIcon, CheckIcon, PencilIcon } from '@heroicons/react/24/outline'
import voiceService from '../../services/voiceService'
import {
  confirmStart,
  confirmSuccess,
  confirmFailure,
  rejectCommand,
  uploadSuccess,
} from '../../store/slices/voiceSlice'
import {
  closeConfirmationDialog,
  openConfirmationDialog,
  showNotification,
} from '../../store/slices/uiSlice'
import MarksPreview from '../marks/MarksPreview'
import QuestionMarksPreview from '../marks/QuestionMarksPreview'
import BatchQuestionMarksPreview from '../marks/BatchQuestionMarksPreview'
import AttendancePreview from '../attendance/AttendancePreview'
import StudentDetailsPreview from '../common/StudentDetailsPreview'
import NavigationPreview from '../common/NavigationPreview'
import ProgressReportPreview from '../common/ProgressReportPreview'
import FeeCollectionPreview from '../fees/FeeCollectionPreview'
import DefaultersPreview from '../fees/DefaultersPreview'
import TodayCollectionPreview from '../fees/TodayCollectionPreview'
import FeeDetailsPreview from '../fees/FeeDetailsPreview'

// Helper function to calculate grade from percentage
const getGradeFromPercentage = (percentage) => {
  if (percentage >= 90) return { grade: 'A+', color: '#16a34a' }
  if (percentage >= 80) return { grade: 'A', color: '#22c55e' }
  if (percentage >= 70) return { grade: 'B+', color: '#84cc16' }
  if (percentage >= 60) return { grade: 'B', color: '#eab308' }
  if (percentage >= 50) return { grade: 'C+', color: '#f97316' }
  if (percentage >= 40) return { grade: 'C', color: '#ef4444' }
  if (percentage >= 33) return { grade: 'D', color: '#dc2626' }
  return { grade: 'F', color: '#991b1b' }
}

// Helper function to convert number to words
const numberToWords = (num) => {
  if (num === 0) return 'Zero'

  const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
                'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
                'Seventeen', 'Eighteen', 'Nineteen']
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

  const convertLessThanThousand = (n) => {
    if (n === 0) return ''
    if (n < 20) return ones[n]
    if (n < 100) return tens[Math.floor(n / 10)] + (n % 10 !== 0 ? ' ' + ones[n % 10] : '')
    return ones[Math.floor(n / 100)] + ' Hundred' + (n % 100 !== 0 ? ' ' + convertLessThanThousand(n % 100) : '')
  }

  if (num < 1000) return convertLessThanThousand(num)
  if (num < 100000) {
    const thousands = Math.floor(num / 1000)
    const remainder = num % 1000
    return convertLessThanThousand(thousands) + ' Thousand' + (remainder !== 0 ? ' ' + convertLessThanThousand(remainder) : '')
  }
  if (num < 10000000) {
    const lakhs = Math.floor(num / 100000)
    const remainder = num % 100000
    return convertLessThanThousand(lakhs) + ' Lakh' + (remainder !== 0 ? ' ' + numberToWords(remainder) : '')
  }
  return num.toString() // Fallback for very large numbers
}

// Generate and download progress report as PDF
const generateAndDownloadReport = (data) => {
  const { student, marks_summary, attendance } = data

  // Create HTML content for the report
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Progress Report - ${student?.name || 'Student'}</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          padding: 40px;
          background: #fff;
          color: #333;
        }
        .report-container { max-width: 800px; margin: 0 auto; }
        .header {
          text-align: center;
          border-bottom: 3px solid #2563eb;
          padding-bottom: 20px;
          margin-bottom: 30px;
        }
        .header h1 { color: #1e40af; font-size: 28px; margin-bottom: 5px; }
        .header h2 { color: #6b7280; font-size: 16px; font-weight: normal; }
        .section {
          margin-bottom: 25px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          overflow: hidden;
        }
        .section-header {
          background: #f3f4f6;
          padding: 12px 20px;
          font-weight: bold;
          color: #374151;
          border-bottom: 1px solid #e5e7eb;
        }
        .section-content { padding: 20px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .info-item { display: flex; }
        .info-label { color: #6b7280; min-width: 120px; }
        .info-value { font-weight: 600; color: #111827; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #f9fafb; font-weight: 600; color: #374151; }
        .total-row { background: #eff6ff; font-weight: bold; }
        .grade-badge {
          display: inline-block;
          padding: 3px 10px;
          color: white;
          border-radius: 12px;
          font-weight: bold;
          font-size: 12px;
        }
        .grade-badge-large {
          display: inline-block;
          padding: 4px 14px;
          background: #2563eb;
          color: white;
          border-radius: 20px;
          font-weight: bold;
          font-size: 14px;
        }
        .marks-in-words {
          font-size: 11px;
          color: #6b7280;
          font-style: italic;
          font-weight: normal;
        }
        .attendance-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; }
        .attendance-item .value { font-size: 32px; font-weight: bold; }
        .attendance-item .label { color: #6b7280; font-size: 14px; }
        .attendance-item.present .value { color: #16a34a; }
        .attendance-item.total .value { color: #6b7280; }
        .attendance-item.percentage .value { color: #2563eb; }
        .footer {
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
          text-align: center;
          color: #9ca3af;
          font-size: 12px;
        }
        @media print {
          body { padding: 20px; }
          .section { break-inside: avoid; }
        }
      </style>
    </head>
    <body>
      <div class="report-container">
        <div class="header">
          <h1>Student Progress Report</h1>
          <h2>Academic Year 2025-26</h2>
        </div>

        <div class="section">
          <div class="section-header">Student Information</div>
          <div class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Name:</span>
                <span class="info-value">${student?.name || 'N/A'}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Roll Number:</span>
                <span class="info-value">${student?.roll_number || 'N/A'}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Class:</span>
                <span class="info-value">${student?.class_name || student?.class + student?.section || 'N/A'}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Report Date:</span>
                <span class="info-value">${new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="section">
          <div class="section-header">Academic Performance</div>
          <div class="section-content">
            ${marks_summary?.subjects && marks_summary.subjects.length > 0 ? `
              <table>
                <thead>
                  <tr>
                    <th>Subject</th>
                    <th>Marks Obtained</th>
                    <th>Maximum Marks</th>
                    <th>Percentage</th>
                    <th>Grade</th>
                  </tr>
                </thead>
                <tbody>
                  ${marks_summary.subjects.map(subject => {
                    const percentage = (subject.marks_obtained / subject.max_marks) * 100
                    const gradeInfo = getGradeFromPercentage(percentage)
                    return `
                    <tr>
                      <td>${subject.name}</td>
                      <td>${subject.marks_obtained}</td>
                      <td>${subject.max_marks}</td>
                      <td>${percentage.toFixed(1)}%</td>
                      <td><span class="grade-badge" style="background: ${gradeInfo.color}">${gradeInfo.grade}</span></td>
                    </tr>
                  `}).join('')}
                  <tr class="total-row">
                    <td>Total</td>
                    <td>
                      ${marks_summary.total_obtained || 0}
                      <div class="marks-in-words">(${numberToWords(marks_summary.total_obtained || 0)})</div>
                    </td>
                    <td>${marks_summary.total_max || 0}</td>
                    <td>${marks_summary.percentage || 0}%</td>
                    <td><span class="grade-badge-large">${marks_summary.grade || getGradeFromPercentage(marks_summary.percentage || 0).grade}</span></td>
                  </tr>
                </tbody>
              </table>
              <div style="margin-top: 15px; text-align: center;">
                <span style="color: #6b7280;">Overall Grade: </span>
                <span class="grade-badge-large">${marks_summary.grade || getGradeFromPercentage(marks_summary.percentage || 0).grade}</span>
              </div>
            ` : '<p style="color: #6b7280; text-align: center;">No marks data available</p>'}
          </div>
        </div>

        <div class="section">
          <div class="section-header">Attendance Summary</div>
          <div class="section-content">
            <div class="attendance-grid">
              <div class="attendance-item present">
                <div class="value">${attendance?.present_count || 0}</div>
                <div class="label">Days Present</div>
              </div>
              <div class="attendance-item total">
                <div class="value">${attendance?.total_sessions || 0}</div>
                <div class="label">Total Days</div>
              </div>
              <div class="attendance-item percentage">
                <div class="value">${attendance?.percentage || 0}%</div>
                <div class="label">Attendance</div>
              </div>
            </div>
          </div>
        </div>

        <div class="footer">
          <p>Generated on ${new Date().toLocaleString('en-IN')} | Audio-to-Action School ERP System</p>
        </div>
      </div>
      <script>
        window.onload = function() {
          window.print();
        }
      </script>
    </body>
    </html>
  `

  // Open in new window and trigger print (which allows Save as PDF)
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(htmlContent)
    printWindow.document.close()
  } else {
    // Fallback: download as HTML file
    const blob = new Blob([htmlContent], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Progress_Report_${student?.name || 'Student'}_${new Date().toISOString().split('T')[0]}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

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

  // State for handling incomplete batch marks
  const [missingMarks, setMissingMarks] = useState({})
  const [showPartialConfirm, setShowPartialConfirm] = useState(false)

  // State for tracking edited confirmation data
  const [editedData, setEditedData] = useState(null)

  // Reset states when dialog opens/closes
  useEffect(() => {
    if (intent === 'BATCH_INCOMPLETE' && confirmationData?.missing_questions) {
      const initialMissing = {}
      confirmationData.missing_questions.forEach(q => {
        initialMissing[q] = ''
      })
      setMissingMarks(initialMissing)
    } else {
      setMissingMarks({})
    }
    // Reset edited data when confirmation data changes
    setEditedData(null)
  }, [intent, confirmationData])

  // Handle updates from preview components
  const handleDataUpdate = (newData) => {
    console.log('[ConfirmationDialog] Data updated:', newData)
    setEditedData(newData)
  }

  // Get the data to use (edited or original)
  const activeData = editedData || confirmationData

  // Auto-close dialog for CANCEL intent
  useEffect(() => {
    if (intent === 'CANCEL' && showConfirmationDialog) {
      console.log('[ConfirmationDialog] CANCEL intent received - auto-closing')
      dispatch(
        showNotification({
          type: 'info',
          message: 'Command cancelled',
        })
      )
      dispatch(closeConfirmationDialog())
      dispatch(rejectCommand())
    }
  }, [intent, showConfirmationDialog, dispatch])

  // Voice command support for confirmation dialog - state declarations
  const [isListeningForConfirm, setIsListeningForConfirm] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('')

  // Refs for voice command callbacks (to avoid stale closures)
  const confirmActionRef = useRef(null)
  const cancelActionRef = useRef(null)

  // Voice command useEffect - MUST be before early return to maintain hook order
  useEffect(() => {
    if (!showConfirmationDialog || !window.webkitSpeechRecognition) {
      setIsListeningForConfirm(false)
      setVoiceStatus('')
      return
    }

    const recognition = new window.webkitSpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-IN'

    recognition.onstart = () => {
      setIsListeningForConfirm(true)
      setVoiceStatus('Listening for "Confirm" or "Cancel"...')
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase().trim()
      console.log('[VoiceConfirm] Heard:', transcript)
      setVoiceStatus(`Heard: "${transcript}"`)

      // Check for confirm commands
      if (transcript.includes('confirm') || transcript.includes('yes') ||
          transcript.includes('okay') || transcript.includes('ok') ||
          transcript.includes('proceed') || transcript.includes('haan') ||
          transcript.includes('theek hai') || transcript.includes('thik hai')) {
        setVoiceStatus('Confirming...')
        if (confirmActionRef.current) confirmActionRef.current()
      }
      // Check for cancel commands
      else if (transcript.includes('cancel') || transcript.includes('no') ||
               transcript.includes('stop') || transcript.includes('reject') ||
               transcript.includes('nahi') || transcript.includes('ruko') ||
               transcript.includes('band karo')) {
        setVoiceStatus('Cancelling...')
        if (cancelActionRef.current) cancelActionRef.current()
      }
      else {
        setVoiceStatus('Say "Confirm" or "Cancel"')
        // Restart listening after a short delay
        setTimeout(() => {
          try { recognition.start() } catch(e) { /* ignore */ }
        }, 1500)
      }
    }

    recognition.onend = () => {
      setIsListeningForConfirm(false)
    }

    recognition.onerror = (event) => {
      console.log('[VoiceConfirm] Error:', event.error)
      setIsListeningForConfirm(false)
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        setVoiceStatus('')
      }
    }

    // Start listening when dialog opens
    const timer = setTimeout(() => {
      try {
        recognition.start()
      } catch (e) {
        console.log('[VoiceConfirm] Could not start:', e)
      }
    }, 800)

    return () => {
      clearTimeout(timer)
      try { recognition.stop() } catch(e) { /* ignore */ }
    }
  }, [showConfirmationDialog])

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

      // Pass edited data if available
      const result = await voiceService.confirmCommand(currentCommand, editedData)

      console.log('Confirm result:', result)
      console.log('Navigation URL:', result?.result?.navigation?.url)
      console.log('Edited data sent:', editedData)

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
        console.log('activeData:', activeData)
        console.log('result:', result)

        const { student, subject, updates } = activeData
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
        console.log('activeData:', activeData)
        console.log('result:', result)

        const { student, subject, question } = activeData
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
        console.log('activeData:', activeData)

        // Extract class, section, roll number, and marks from activeData (which may be edited)
        const { student, marks_table } = activeData

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

      // Handle download progress report
      if (intent === 'DOWNLOAD_PROGRESS_REPORT') {
        console.log('=== GENERATING PROGRESS REPORT PDF ===')
        const reportData = result?.result || confirmationData
        generateAndDownloadReport(reportData)
      }

      // Handle navigation if it's a navigation command
      // Check both result.navigation and confirmationData.url for the navigation URL
      const navigationUrl = result?.result?.navigation?.url || confirmationData?.url
      const isNavigationIntent = [
        'NAVIGATE_MARKS', 'NAVIGATE_ATTENDANCE', 'NAVIGATE_DASHBOARD', 'NAVIGATE_REPORTS',
        'NAVIGATE_CLASS_REPORT', 'NAVIGATE_STUDENT_REPORT', 'NAVIGATE_ATTENDANCE_REPORT',
        'OPEN_MARKS_SHEET', 'OPEN_ATTENDANCE_SHEET', 'OPEN_QUESTION_SHEET', 'SELECT_EXAM_TYPE',
        'OPEN_FEE_PAGE', 'NAVIGATE_FEE_REPORTS', 'SHOW_DEFAULTERS', 'TODAY_COLLECTION'
      ].includes(intent)

      if (navigationUrl && isNavigationIntent) {
        console.log('Navigating to:', navigationUrl)
        setTimeout(() => {
          navigate(navigationUrl)
        }, 500) // Small delay to show success notification
      } else if (result?.result?.navigation?.url) {
        // Fallback for other commands that return navigation
        console.log('Navigating to (from result):', result.result.navigation.url)
        setTimeout(() => {
          navigate(result.result.navigation.url)
        }, 500)
      } else {
        console.log('No navigation URL found in result or confirmationData')

        // For marks/attendance commands, trigger events to update the page
        if (intent === 'MARK_ATTENDANCE') {
          console.log('Attendance marked via voice command:', result)
          // Dispatch custom event for attendance page to refresh
          window.dispatchEvent(new CustomEvent('attendanceUpdated', {
            detail: {
              classSection: confirmationData?.class_section,
              markedCount: result?.result?.marked_count,
              status: confirmationData?.status,
              excludedRolls: confirmationData?.excluded_rolls
            }
          }))
          // Show more detailed success message
          dispatch(
            showNotification({
              type: 'success',
              message: `Attendance marked: ${result?.result?.marked_count || 0} students marked as ${confirmationData?.status || 'PRESENT'}`,
            })
          )
        } else if (intent === 'UPDATE_MARKS' || intent === 'ENTER_MARKS') {
          console.log('Marks updated - page will reflect changes via localStorage')
          // The storage event was already dispatched above
        } else if (intent === 'COLLECT_FEE') {
          console.log('Fee collected via voice command - dispatching refresh event')
          window.dispatchEvent(new CustomEvent('feeCollected', {
            detail: {
              student: confirmationData?.student,
              amount: editedData?.amount || confirmationData?.amount,
              paymentMethod: editedData?.payment_method || confirmationData?.payment_method,
            }
          }))
          // Dispatch receipt event after a short delay so dialog can close first
          const receiptResult = result?.result || {}
          setTimeout(() => {
            window.dispatchEvent(new CustomEvent('voiceReceiptReady', {
              detail: {
                receiptNumber: receiptResult.receipt_number || '',
                studentName: receiptResult.student_name || confirmationData?.student?.name || '',
                rollNumber: receiptResult.roll_number || confirmationData?.student?.roll_number || '',
                className: receiptResult.class_name || confirmationData?.student?.class || '',
                amount: receiptResult.amount || editedData?.amount || confirmationData?.amount || 0,
                paymentMethod: receiptResult.payment_method || editedData?.payment_method || confirmationData?.payment_method || 'Cash',
                feeType: receiptResult.fee_type_display || '',
                date: receiptResult.payment_date || new Date().toLocaleDateString('en-IN'),
                time: receiptResult.payment_time || new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
                collectedBy: receiptResult.collected_by_name || '',
              }
            }))
          }, 300)
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

  // Alias for voice command
  const handleCancel = handleReject

  // Update refs for voice command callbacks
  confirmActionRef.current = handleConfirm
  cancelActionRef.current = handleCancel

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
      case 'DATA_NOT_FOUND':
        return (
          <div className="space-y-4">
            <div className="bg-amber-50 border border-amber-300 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-amber-800 font-semibold text-lg mb-2">Data Not Found</h3>
                  <p className="text-amber-700 mb-4">{confirmationData.message}</p>
                  <div className="bg-white rounded-lg p-3 border border-amber-200">
                    <p className="text-sm text-gray-600 font-semibold mb-2">Suggestions:</p>
                    <ul className="space-y-1">
                      {confirmationData.suggestions?.map((suggestion, idx) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start">
                          <span className="text-amber-500 mr-2">•</span>
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      case 'SELECT_STUDENT':
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 font-medium mb-4">{confirmationData.message}</p>
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {confirmationData.students?.map((student) => (
                  <button
                    key={student.id}
                    onClick={async () => {
                      try {
                        dispatch(closeConfirmationDialog())
                        dispatch(showNotification({ type: 'info', message: `Loading fee details for ${student.name}...` }))

                        // Build transcript based on the original intent type
                        let transcript
                        if (confirmationData.intent_type === 'SHOW_FEE_DETAILS') {
                          transcript = `show fee details of student ${student.roll_number} class ${student.class_grade}${student.section_name}`
                        } else {
                          transcript = `collect ${confirmationData.amount} from roll ${student.roll_number} class ${student.class_grade}${student.section_name} ${confirmationData.payment_method || 'cash'}`
                        }

                        const fakeBlob = new Blob([new Uint8Array(1)], { type: 'audio/webm' })
                        const result = await voiceService.uploadVoiceCommand(fakeBlob, {}, transcript)

                        if (result.intent && result.confirmation_data) {
                          dispatch(uploadSuccess({
                            command_id: result.command_id,
                            transcription: result.transcription,
                            intent: result.intent,
                            confirmation_data: result.confirmation_data,
                          }))
                          dispatch(openConfirmationDialog())
                        }
                      } catch (err) {
                        console.error('Student select error:', err)
                        dispatch(showNotification({ type: 'error', message: err.message || 'Failed to load student fee details' }))
                      }
                    }}
                    className="w-full text-left px-4 py-3 bg-white border-2 border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition-all"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-semibold text-gray-900">{student.name}</span>
                        <span className="text-sm text-gray-500 ml-2">Roll {student.roll_number}</span>
                      </div>
                      <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                        Class {student.class}
                      </span>
                    </div>
                    {student.father_name && (
                      <p className="text-xs text-gray-400 mt-1">Father: {student.father_name}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )
      case 'SELECT_SECTION':
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 font-medium mb-4">{confirmationData.message}</p>
              <div className="grid grid-cols-3 gap-3">
                {confirmationData.sections?.map((section) => (
                  <button
                    key={section.name}
                    onClick={() => {
                      dispatch(closeConfirmationDialog())
                      dispatch(rejectCommand())
                      navigate(section.url)
                      dispatch(showNotification({
                        type: 'success',
                        message: `Navigating to Class ${confirmationData.class_name} ${section.display}`,
                      }))
                    }}
                    className="px-6 py-4 bg-white border-2 border-blue-300 text-blue-700 rounded-lg hover:bg-blue-100 hover:border-blue-500 transition-all font-semibold text-lg shadow-sm"
                  >
                    {section.display}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )
      case 'BATCH_UPDATE_QUESTION_MARKS':
        return <BatchQuestionMarksPreview data={activeData} onUpdate={handleDataUpdate} />
      case 'UPDATE_QUESTION_MARKS':
        return <QuestionMarksPreview data={activeData} onUpdate={handleDataUpdate} />
      case 'ENTER_MARKS':
      case 'UPDATE_MARKS':
        return <MarksPreview data={activeData} onUpdate={handleDataUpdate} />
      case 'MARK_ATTENDANCE':
        return <AttendancePreview data={confirmationData} />
      case 'VIEW_STUDENT':
        return <StudentDetailsPreview data={confirmationData} />
      case 'COLLECT_FEE':
        return <FeeCollectionPreview data={activeData} onUpdate={handleDataUpdate} />
      case 'SHOW_FEE_DETAILS':
        return <FeeDetailsPreview data={confirmationData} />
      case 'SHOW_DEFAULTERS':
        return <DefaultersPreview data={confirmationData} />
      case 'TODAY_COLLECTION':
        return <TodayCollectionPreview data={confirmationData} />
      case 'NAVIGATE_MARKS':
      case 'NAVIGATE_ATTENDANCE':
      case 'NAVIGATE_DASHBOARD':
      case 'NAVIGATE_REPORTS':
      case 'NAVIGATE_CLASS_REPORT':
      case 'NAVIGATE_STUDENT_REPORT':
      case 'NAVIGATE_ATTENDANCE_REPORT':
      case 'OPEN_MARKS_SHEET':
      case 'OPEN_ATTENDANCE_SHEET':
      case 'OPEN_QUESTION_SHEET':
      case 'SELECT_EXAM_TYPE':
      case 'OPEN_FEE_PAGE':
      case 'NAVIGATE_FEE_REPORTS':
        return <NavigationPreview data={confirmationData} />
      case 'DOWNLOAD_PROGRESS_REPORT':
        return <ProgressReportPreview data={confirmationData} />
      case 'INCOMPLETE':
        return (
          <div className="space-y-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <p className="text-orange-800 font-medium mb-3">{confirmationData.message}</p>
              {confirmationData.missing && confirmationData.missing.length > 0 && (
                <div className="mb-3">
                  <p className="text-sm text-orange-700 font-semibold">Missing:</p>
                  <ul className="list-disc list-inside text-sm text-orange-600">
                    {confirmationData.missing.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="space-y-2">
                <p className="text-sm text-gray-600 font-semibold">Try these examples:</p>
                {confirmationData.examples?.map((example, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span className="text-gray-700 text-sm">{example}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      case 'BATCH_INCOMPLETE':
        return (
          <div className="space-y-4">
            {/* Paired updates - successfully matched */}
            {confirmationData.paired_updates && confirmationData.paired_updates.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-medium mb-3">Successfully matched ({confirmationData.paired_updates.length} questions):</p>
                <div className="grid grid-cols-5 gap-2">
                  {confirmationData.paired_updates.map((update, idx) => (
                    <div key={idx} className="bg-white rounded p-2 border border-green-200 text-center">
                      <span className="text-xs text-gray-500">Q{update.question_number}</span>
                      <p className="font-bold text-green-700">{update.marks_obtained}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing marks - editable inputs */}
            {confirmationData.missing_questions && confirmationData.missing_questions.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 font-medium mb-3">
                  <PencilIcon className="w-4 h-4 inline mr-1" />
                  Missing marks for {confirmationData.missing_questions.length} question(s):
                </p>
                <div className="grid grid-cols-5 gap-2 mb-3">
                  {confirmationData.missing_questions.map((qNum) => (
                    <div key={qNum} className="bg-white rounded p-2 border border-yellow-300">
                      <label className="text-xs text-gray-500 block text-center">Q{qNum}</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        placeholder="?"
                        value={missingMarks[qNum] || ''}
                        onChange={(e) => setMissingMarks(prev => ({
                          ...prev,
                          [qNum]: e.target.value
                        }))}
                        className="w-full text-center font-bold text-yellow-700 border-0 border-b-2 border-yellow-300 focus:border-yellow-500 focus:ring-0 bg-transparent"
                      />
                    </div>
                  ))}
                </div>
                <p className="text-xs text-yellow-600">
                  Fill in the missing marks above, or say "Question {confirmationData.missing_questions[0]} mark is 5"
                </p>
              </div>
            )}

            {/* Extra marks warning */}
            {confirmationData.extra_marks && confirmationData.extra_marks.length > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-orange-800 font-medium mb-2">Extra marks (will be ignored):</p>
                <p className="text-orange-600">{confirmationData.extra_marks.join(', ')}</p>
              </div>
            )}

            {/* Options */}
            <div className="bg-gray-50 rounded-lg p-3 text-sm">
              <p className="font-medium text-gray-700 mb-2">Options:</p>
              <ul className="text-gray-600 space-y-1">
                <li>• Fill in missing marks above and click Confirm</li>
                <li>• Click "Confirm Partial" to save only matched questions</li>
                <li>• Say the missing marks: "Question {confirmationData.missing_questions?.[0] || 'X'} is 5"</li>
              </ul>
            </div>
          </div>
        )
      case 'BATCH_VALIDATION_ERROR':
        return (
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 font-medium mb-3">{confirmationData.message}</p>
              {confirmationData.details && (
                <div className="mb-3 bg-white rounded p-3 border border-red-100">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600 font-semibold">Questions ({confirmationData.details.questions_count}):</p>
                      <p className="text-gray-800">{confirmationData.details.questions?.join(', ')}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 font-semibold">Marks ({confirmationData.details.marks_count}):</p>
                      <p className="text-gray-800">{confirmationData.details.marks?.join(', ')}</p>
                    </div>
                  </div>
                </div>
              )}
              <div className="space-y-2">
                <p className="text-sm text-gray-600 font-semibold">Correct format:</p>
                {confirmationData.examples?.map((example, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="text-red-600 font-bold">•</span>
                    <span className="text-gray-700 text-sm">{example}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
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
        <div className="bg-gray-50 px-6 py-4 rounded-b-lg">
          {/* Voice command status */}
          {voiceStatus && (
            <div className={`mb-3 text-center text-sm ${isListeningForConfirm ? 'text-blue-600' : 'text-gray-600'}`}>
              <div className="flex items-center justify-center space-x-2">
                {isListeningForConfirm && (
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                  </span>
                )}
                <span>🎤 {voiceStatus}</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">Say "Confirm" or "Cancel" to proceed by voice</p>
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <XMarkIcon className="w-5 h-5" />
              <span>{(intent === 'CLARIFY' || intent === 'INCOMPLETE' || intent === 'BATCH_VALIDATION_ERROR' || intent === 'SELECT_SECTION' || intent === 'SELECT_STUDENT' || intent === 'DATA_NOT_FOUND') ? (intent === 'SELECT_SECTION' || intent === 'SELECT_STUDENT' ? 'Close' : 'OK') : 'Cancel'}</span>
            </button>

          {/* Special buttons for BATCH_INCOMPLETE */}
          {intent === 'BATCH_INCOMPLETE' && (
            <>
              <button
                onClick={() => {
                  // Confirm only the paired updates, ignore missing
                  handleConfirm()
                }}
                disabled={isProcessing || !confirmationData?.paired_updates?.length}
                className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <CheckIcon className="w-5 h-5" />
                <span>Confirm Partial ({confirmationData?.paired_updates?.length || 0})</span>
              </button>
              <button
                onClick={() => {
                  // Check if all missing marks are filled
                  const allFilled = confirmationData?.missing_questions?.every(q => missingMarks[q] && missingMarks[q] !== '')
                  if (allFilled) {
                    // TODO: Add the missing marks to the confirmation data and confirm
                    handleConfirm()
                  } else {
                    dispatch(showNotification({
                      type: 'warning',
                      message: 'Please fill in all missing marks first',
                    }))
                  }
                }}
                disabled={isProcessing}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <CheckIcon className="w-5 h-5" />
                <span>Confirm All</span>
              </button>
            </>
          )}

          {intent !== 'CLARIFY' && intent !== 'INCOMPLETE' && intent !== 'BATCH_VALIDATION_ERROR' && intent !== 'SELECT_SECTION' && intent !== 'SELECT_STUDENT' && intent !== 'BATCH_INCOMPLETE' && intent !== 'DATA_NOT_FOUND' && (
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
    </div>
  )
}

export default ConfirmationDialog
