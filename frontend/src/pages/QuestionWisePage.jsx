import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { ArrowLeftIcon, CheckIcon, PencilIcon } from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import api from '../services/api'

const QuestionWisePage = () => {
  const { classNum, section, rollNumber, subjectId } = useParams()
  const navigate = useNavigate()
  const dispatch = useDispatch()

  // Voice command state
  const { lastConfirmedCommand } = useSelector((state) => state.voice)

  const [questions, setQuestions] = useState([])
  const [student, setStudent] = useState(null)
  const [subject, setSubject] = useState(null)
  const [editingCell, setEditingCell] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [examType] = useState('UNIT_TEST')
  const [highlightedQuestion, setHighlightedQuestion] = useState(null)

  // Subject mapping
  const subjects = {
    '1': { id: 1, name: 'Mathematics', code: 'MATH' },
    '2': { id: 2, name: 'Hindi', code: 'HINDI' },
    '3': { id: 3, name: 'English', code: 'ENGLISH' },
    '4': { id: 4, name: 'Science', code: 'SCIENCE' },
    '5': { id: 5, name: 'Social Studies', code: 'SOCIAL' }
  }

  useEffect(() => {
    // Set student and subject info
    setStudent({
      rollNumber: parseInt(rollNumber),
      name: `Student ${rollNumber}`,
      className: `${classNum}${section}`
    })
    setSubject(subjects[subjectId])

    // Load existing question marks from localStorage
    loadQuestions()
  }, [classNum, section, rollNumber, subjectId])

  // Listen for voice command confirmations
  useEffect(() => {
    // Handle SINGLE question update
    if (lastConfirmedCommand?.intent === 'UPDATE_QUESTION_MARKS') {
      const { question, student: voiceStudent } = lastConfirmedCommand.confirmationData || {}

      // Check if this command is for the current student/subject
      if (voiceStudent?.roll_number === parseInt(rollNumber)) {
        const questionNumber = question?.number
        const marksObtained = lastConfirmedCommand.result?.marks_obtained

        if (questionNumber && marksObtained !== undefined) {
          // Update the specific question
          setQuestions(prev => prev.map(q => {
            if (q.questionNumber === questionNumber) {
              return { ...q, marksObtained: parseFloat(marksObtained) }
            }
            return q
          }))

          // Highlight the updated question
          setHighlightedQuestion(questionNumber)
          setTimeout(() => setHighlightedQuestion(null), 3000)

          // Auto-save after voice command
          setTimeout(() => {
            handleSaveAll()
          }, 1000)
        }
      }
    }

    // Handle BATCH question updates
    if (lastConfirmedCommand?.intent === 'BATCH_UPDATE_QUESTION_MARKS') {
      const { student: voiceStudent } = lastConfirmedCommand.confirmationData || {}
      const updatesApplied = lastConfirmedCommand.result?.updates || []

      // Check if this command is for the current student/subject
      if (voiceStudent?.roll_number === parseInt(rollNumber)) {
        console.log('[QuestionWisePage] Applying batch updates:', updatesApplied)

        // Update all affected questions
        setQuestions(prev => prev.map(q => {
          const update = updatesApplied.find(u => u.question_number === q.questionNumber)
          if (update) {
            return { ...q, marksObtained: parseFloat(update.marks_obtained) }
          }
          return q
        }))

        // Highlight all updated questions
        const updatedQuestionNumbers = updatesApplied.map(u => u.question_number)
        setHighlightedQuestion(updatedQuestionNumbers)
        setTimeout(() => setHighlightedQuestion(null), 3000)

        // Auto-save after voice command
        setTimeout(() => {
          handleSaveAll()
        }, 1000)
      }
    }
  }, [lastConfirmedCommand])

  const loadQuestions = () => {
    const storageKey = `questionMarks_${classNum}${section}_${examType}`
    const savedData = localStorage.getItem(storageKey)

    if (savedData) {
      const allQuestionMarks = JSON.parse(savedData)
      const studentQuestions = allQuestionMarks?.[rollNumber]?.[subjectId]?.questions || {}

      // Convert to array format
      const questionsArray = Array.from({ length: 10 }, (_, i) => ({
        questionNumber: i + 1,
        maxMarks: studentQuestions[i + 1]?.maxMarks || 10,
        marksObtained: studentQuestions[i + 1]?.marksObtained || 0
      }))

      setQuestions(questionsArray)
    } else {
      // Initialize default 10 questions
      const defaultQuestions = Array.from({ length: 10 }, (_, i) => ({
        questionNumber: i + 1,
        maxMarks: 10,
        marksObtained: 0
      }))
      setQuestions(defaultQuestions)
    }
  }

  const calculateGrandTotal = () => {
    return questions.reduce((sum, q) => sum + q.marksObtained, 0)
  }

  const calculateMaxTotal = () => {
    return questions.reduce((sum, q) => sum + q.maxMarks, 0)
  }

  const handleCellClick = (questionNumber, field) => {
    setEditingCell({ questionNumber, field })
  }

  const handleCellChange = (questionNumber, field, value) => {
    const numValue = parseFloat(value) || 0
    setQuestions(prev => prev.map(q => {
      if (q.questionNumber === questionNumber) {
        const updated = { ...q, [field]: numValue }
        // Validate: obtained can't exceed max
        if (field === 'marksObtained' && numValue > q.maxMarks) {
          return q
        }
        return updated
      }
      return q
    }))
  }

  const handleSaveCell = () => {
    setEditingCell(null)
  }

  const handleSaveAll = async () => {
    setSaving(true)
    try {
      const grandTotal = calculateGrandTotal()

      // Save to question-wise localStorage
      const questionStorageKey = `questionMarks_${classNum}${section}_${examType}`
      const existingQuestionData = JSON.parse(localStorage.getItem(questionStorageKey) || '{}')

      if (!existingQuestionData[rollNumber]) {
        existingQuestionData[rollNumber] = {}
      }
      if (!existingQuestionData[rollNumber][subjectId]) {
        existingQuestionData[rollNumber][subjectId] = { questions: {} }
      }

      // Convert questions array to object
      const questionsObj = {}
      questions.forEach(q => {
        questionsObj[q.questionNumber] = {
          maxMarks: q.maxMarks,
          marksObtained: q.marksObtained
        }
      })

      existingQuestionData[rollNumber][subjectId].questions = questionsObj
      existingQuestionData[rollNumber][subjectId].total = grandTotal

      localStorage.setItem(questionStorageKey, JSON.stringify(existingQuestionData))

      // Update main marks localStorage with grand total
      const marksStorageKey = `marks_${classNum}${section}_${examType}`
      const existingMarks = JSON.parse(localStorage.getItem(marksStorageKey) || '{}')

      if (!existingMarks[rollNumber]) {
        existingMarks[rollNumber] = {}
      }
      existingMarks[rollNumber][subjectId] = grandTotal

      localStorage.setItem(marksStorageKey, JSON.stringify(existingMarks))

      // Dispatch storage event to notify MarksSheetPage
      window.dispatchEvent(new StorageEvent('storage', {
        key: marksStorageKey,
        newValue: JSON.stringify(existingMarks),
        url: window.location.href
      }))

      // TODO: Save to API
      // await api.post('/marks/question-marks/bulk-update/', {
      //   marks_id: marksId,
      //   questions: questions.map(q => ({
      //     question_number: q.questionNumber,
      //     max_marks: q.maxMarks,
      //     marks_obtained: q.marksObtained
      //   }))
      // })

      // Navigate back to marksheet with updated data
      setTimeout(() => {
        navigate(`/marks/${classNum}/${section}`, {
          state: {
            updated: true,
            rollNumber: parseInt(rollNumber),
            subjectId: parseInt(subjectId),
            grandTotal
          }
        })
      }, 500)

    } catch (error) {
      console.error('Error saving questions:', error)
      alert('Failed to save question marks')
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    navigate(`/marks/${classNum}/${section}`)
  }

  if (!student || !subject) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  const grandTotal = calculateGrandTotal()
  const maxTotal = calculateMaxTotal()

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={handleCancel}
            className="flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Marksheet
          </button>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Question-Wise Marks Entry
            </h1>
            <div className="text-sm text-gray-600">
              <p><strong>Student:</strong> {student.name} (Roll {student.rollNumber})</p>
              <p><strong>Class:</strong> {classNum}{section}</p>
              <p><strong>Subject:</strong> {subject.name}</p>
              <p><strong>Exam Type:</strong> Unit Test</p>
            </div>
          </div>
        </div>

        {/* Questions Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Question
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Max Marks
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Marks Obtained
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {questions.map((question) => {
                  // Check if this question is highlighted (supports both single number and array)
                  const isHighlighted = Array.isArray(highlightedQuestion)
                    ? highlightedQuestion.includes(question.questionNumber)
                    : highlightedQuestion === question.questionNumber

                  return (
                    <tr
                      key={question.questionNumber}
                      className={`hover:bg-gray-50 transition-colors ${
                        isHighlighted
                          ? 'bg-green-100 border-2 border-green-500'
                          : ''
                      }`}
                    >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Q{question.questionNumber}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {editingCell?.questionNumber === question.questionNumber && editingCell?.field === 'maxMarks' ? (
                        <div className="flex items-center justify-center space-x-2">
                          <input
                            type="number"
                            step="0.5"
                            value={question.maxMarks}
                            onChange={(e) => handleCellChange(question.questionNumber, 'maxMarks', e.target.value)}
                            className="w-20 px-2 py-1 border border-blue-500 rounded focus:ring-2 focus:ring-blue-500 text-center"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveCell()
                              if (e.key === 'Escape') setEditingCell(null)
                            }}
                          />
                          <button
                            onClick={handleSaveCell}
                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                          >
                            <CheckIcon className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleCellClick(question.questionNumber, 'maxMarks')}
                          className="inline-flex items-center px-3 py-1 rounded hover:bg-blue-50 group"
                        >
                          <span className="text-sm font-semibold">{question.maxMarks}</span>
                          <PencilIcon className="w-4 h-4 ml-2 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {editingCell?.questionNumber === question.questionNumber && editingCell?.field === 'marksObtained' ? (
                        <div className="flex items-center justify-center space-x-2">
                          <input
                            type="number"
                            step="0.5"
                            value={question.marksObtained}
                            onChange={(e) => handleCellChange(question.questionNumber, 'marksObtained', e.target.value)}
                            max={question.maxMarks}
                            className="w-20 px-2 py-1 border border-blue-500 rounded focus:ring-2 focus:ring-blue-500 text-center"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveCell()
                              if (e.key === 'Escape') setEditingCell(null)
                            }}
                          />
                          <button
                            onClick={handleSaveCell}
                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                          >
                            <CheckIcon className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleCellClick(question.questionNumber, 'marksObtained')}
                          className="inline-flex items-center px-3 py-1 rounded hover:bg-blue-50 group"
                        >
                          <span className="text-sm font-semibold">{question.marksObtained}</span>
                          <PencilIcon className="w-4 h-4 ml-2 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </button>
                      )}
                    </td>
                  </tr>
                  )
                })}
                {/* Grand Total Row */}
                <tr className="bg-blue-50 font-bold">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Grand Total
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {maxTotal}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-blue-600">
                    {grandTotal}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Action Buttons */}
          <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3">
            <button
              onClick={handleCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveAll}
              disabled={saving}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save & Return to Marksheet'}
            </button>
          </div>
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> Click on any cell to edit. Press Enter to save or Escape to cancel.
            <br />
            <strong>Voice Tip:</strong> Use the microphone button to update questions via voice command!
            <br />
            Example: "Update question 3 to 8 marks" or "Change question 5 to 7.5 marks"
            <br />
            The grand total ({grandTotal}) will automatically update the subject marks in the main marksheet when you save.
          </p>
        </div>
      </div>

      {/* Floating Voice Button */}
      <FloatingVoiceButton />

      {/* Confirmation Dialog */}
      <ConfirmationDialog />
    </div>
  )
}

export default QuestionWisePage
