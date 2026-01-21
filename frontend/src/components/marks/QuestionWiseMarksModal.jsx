import React, { useState, useEffect } from 'react'
import { XMarkIcon, CheckIcon, PencilIcon } from '@heroicons/react/24/outline'
import api from '../../services/api'

const QuestionWiseMarksModal = ({
  isOpen,
  onClose,
  student,
  subject,
  marksId,
  examType = 'UNIT_TEST',
  onTotalUpdate
}) => {
  const [questions, setQuestions] = useState([])
  const [editingCell, setEditingCell] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  // Initialize questions (default 10 questions)
  useEffect(() => {
    if (isOpen && marksId) {
      loadQuestions()
    }
  }, [isOpen, marksId])

  const loadQuestions = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/marks/question-marks/?marks_id=${marksId}`)

      if (response.data && response.data.length > 0) {
        // Load existing questions
        setQuestions(response.data.map(q => ({
          id: q.id,
          questionNumber: q.question_number,
          maxMarks: parseFloat(q.max_marks),
          marksObtained: parseFloat(q.marks_obtained)
        })))
      } else {
        // Initialize default 10 questions
        const defaultQuestions = Array.from({ length: 10 }, (_, i) => ({
          id: null,
          questionNumber: i + 1,
          maxMarks: 10,
          marksObtained: 0
        }))
        setQuestions(defaultQuestions)
      }
    } catch (error) {
      console.error('Error loading questions:', error)
      // Initialize default on error
      const defaultQuestions = Array.from({ length: 10 }, (_, i) => ({
        id: null,
        questionNumber: i + 1,
        maxMarks: 10,
        marksObtained: 0
      }))
      setQuestions(defaultQuestions)
    } finally {
      setLoading(false)
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
          return q // Don't update if invalid
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
      // Prepare data for bulk update
      const questionsData = questions.map(q => ({
        question_number: q.questionNumber,
        max_marks: q.maxMarks,
        marks_obtained: q.marksObtained
      }))

      const response = await api.post('/marks/question-marks/bulk-update/', {
        marks_id: marksId,
        questions: questionsData
      })

      if (response.data.success) {
        const grandTotal = calculateGrandTotal()

        // Update localStorage
        updateLocalStorage(grandTotal)

        // Notify parent component
        if (onTotalUpdate) {
          onTotalUpdate(student.rollNumber, subject.id, grandTotal)
        }

        // Close modal
        onClose()
      }
    } catch (error) {
      console.error('Error saving questions:', error)
      alert('Failed to save question marks')
    } finally {
      setSaving(false)
    }
  }

  const updateLocalStorage = (grandTotal) => {
    const storageKey = `marks_${student.className.match(/(\d+)([A-Z])/)?.[1] || ''}${student.className.match(/(\d+)([A-Z])/)?.[2] || ''}_${examType}`
    const existingMarks = JSON.parse(localStorage.getItem(storageKey) || '{}')

    if (!existingMarks[student.rollNumber]) {
      existingMarks[student.rollNumber] = {}
    }

    existingMarks[student.rollNumber][subject.id] = grandTotal
    localStorage.setItem(storageKey, JSON.stringify(existingMarks))

    // Dispatch storage event
    window.dispatchEvent(new StorageEvent('storage', {
      key: storageKey,
      newValue: JSON.stringify(existingMarks),
      url: window.location.href
    }))
  }

  if (!isOpen) return null

  const grandTotal = calculateGrandTotal()
  const maxTotal = calculateMaxTotal()

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Question-wise Marks Entry
                </h3>
                <p className="text-sm text-blue-100 mt-1">
                  {student?.name} (Roll {student?.rollNumber}) - {subject?.name}
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading questions...</p>
              </div>
            ) : (
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
                    {questions.map((question) => (
                      <tr key={question.questionNumber} className="hover:bg-gray-50">
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
                    ))}
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
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveAll}
              disabled={saving}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save All Questions'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default QuestionWiseMarksModal
