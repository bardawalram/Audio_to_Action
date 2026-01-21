import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeftIcon, PencilIcon, CheckIcon, XMarkIcon, ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'

const MarksSheetPage = () => {
  const { classNum, section } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [students, setStudents] = useState([])
  const [marks, setMarks] = useState({})
  const [editingCell, setEditingCell] = useState(null)
  const [examType, setExamType] = useState(location.state?.examType || 'UNIT_TEST')

  const subjects = [
    { id: 1, name: 'Mathematics', maxMarks: 100 },
    { id: 2, name: 'Hindi', maxMarks: 100 },
    { id: 3, name: 'English', maxMarks: 100 },
    { id: 4, name: 'Science', maxMarks: 100 },
    { id: 5, name: 'Social Studies', maxMarks: 100 }
  ]

  useEffect(() => {
    console.log('=== MARKSSHEETPAGE USEEFFECT ===')
    console.log('classNum:', classNum, 'section:', section, 'examType:', examType)

    // Generate dummy students (20 per class)
    const studentList = []
    for (let i = 1; i <= 20; i++) {
      studentList.push({
        id: i,
        rollNumber: i,
        name: `Student ${i}`,
        className: `${classNum}${section}`
      })
    }
    setStudents(studentList)

    // Initialize marks - use localStorage to persist across reloads
    const storageKey = `marks_${classNum}${section}_${examType}`
    console.log('storageKey:', storageKey)

    const loadMarks = () => {
      const savedMarks = localStorage.getItem(storageKey)
      console.log('savedMarks from localStorage:', savedMarks)

      if (savedMarks) {
        // Load saved marks
        const parsedMarks = JSON.parse(savedMarks)
        console.log('Loading marks from localStorage:', parsedMarks)
        setMarks(parsedMarks)
      } else {
        // Initialize with zeros - USE ROLLNUMBER AS KEY (not id)
        console.log('No saved marks found, initializing with zeros')
        const initialMarks = {}
        studentList.forEach(student => {
          initialMarks[student.rollNumber] = {}
          subjects.forEach(subject => {
            initialMarks[student.rollNumber][subject.id] = 0
          })
        })
        setMarks(initialMarks)
        localStorage.setItem(storageKey, JSON.stringify(initialMarks))
        console.log('Initialized and saved marks:', initialMarks)
      }
    }

    loadMarks()

    // Listen for storage events (when marks are updated via voice commands)
    const handleStorageChange = (e) => {
      if (e.key === storageKey || e.type === 'storage') {
        console.log('Storage changed, reloading marks...')
        loadMarks()
      }
    }

    window.addEventListener('storage', handleStorageChange)

    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [classNum, section, examType])

  // Listen for navigation state updates from QuestionWisePage
  useEffect(() => {
    if (location.state?.updated && location.state?.rollNumber && location.state?.subjectId && location.state?.grandTotal !== undefined) {
      const { rollNumber, subjectId, grandTotal } = location.state

      console.log('=== LIVE UPDATE FROM NAVIGATION STATE ===')
      console.log('Updating marks for Roll:', rollNumber, 'Subject:', subjectId, 'Total:', grandTotal)

      // Update the marks state immediately (in-memory)
      setMarks(prev => ({
        ...prev,
        [rollNumber]: {
          ...prev[rollNumber],
          [subjectId]: grandTotal
        }
      }))

      // Clear the navigation state to prevent re-applying on re-render
      navigate(location.pathname, { replace: true, state: {} })
    }
  }, [location.state])

  const handleCellClick = (rollNumber, subjectId) => {
    // Navigate to question-wise page
    navigate(`/marks/${classNum}/${section}/question/${rollNumber}/${subjectId}`)
  }

  const handleMarkChange = (rollNumber, subjectId, value) => {
    const numValue = parseInt(value) || 0
    const subject = subjects.find(s => s.id === subjectId)

    if (numValue >= 0 && numValue <= subject.maxMarks) {
      setMarks(prev => ({
        ...prev,
        [rollNumber]: {
          ...prev[rollNumber],
          [subjectId]: numValue
        }
      }))
    }
  }

  const handleSaveCell = () => {
    setEditingCell(null)
    // Save to localStorage
    const storageKey = `marks_${classNum}${section}_${examType}`
    localStorage.setItem(storageKey, JSON.stringify(marks))
    console.log('Saved marks to localStorage:', marks)
  }

  const handleCancelEdit = () => {
    setEditingCell(null)
  }

  const calculateTotal = (rollNumber) => {
    return subjects.reduce((sum, subject) => sum + (marks[rollNumber]?.[subject.id] || 0), 0)
  }

  const calculatePercentage = (rollNumber) => {
    const total = calculateTotal(rollNumber)
    const maxTotal = subjects.reduce((sum, subject) => sum + subject.maxMarks, 0)
    return ((total / maxTotal) * 100).toFixed(2)
  }

  const getGrade = (percentage) => {
    if (percentage >= 90) return { grade: 'A+', color: 'text-green-600' }
    if (percentage >= 80) return { grade: 'A', color: 'text-green-600' }
    if (percentage >= 70) return { grade: 'B+', color: 'text-blue-600' }
    if (percentage >= 60) return { grade: 'B', color: 'text-blue-600' }
    if (percentage >= 50) return { grade: 'C', color: 'text-yellow-600' }
    if (percentage >= 40) return { grade: 'D', color: 'text-orange-600' }
    return { grade: 'F', color: 'text-red-600' }
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-white shadow sticky top-0 z-10">
        <div className="max-w-full px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/marks')}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Marks Sheet - Class {classNum}{section}
                </h1>
                <p className="text-gray-500">
                  {examType === 'UNIT_TEST' ? 'Unit Test' : examType === 'MIDTERM' ? 'Midterm Exam' : 'Final Exam'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-full px-4 py-8">
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                  Roll No
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Student Name
                </th>
                {subjects.map(subject => (
                  <th key={subject.id} className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {subject.name}
                    <br />
                    <span className="text-xs text-gray-400">({subject.maxMarks})</span>
                  </th>
                ))}
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Percentage
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Grade
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {students.map((student) => {
                const percentage = calculatePercentage(student.rollNumber)
                const { grade, color } = getGrade(percentage)

                return (
                  <tr key={student.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-white">
                      {student.rollNumber}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {student.name}
                    </td>
                    {subjects.map(subject => {
                      const isEditing = editingCell?.studentId === student.id && editingCell?.subjectId === subject.id
                      const mark = marks[student.rollNumber]?.[subject.id] || 0

                      return (
                        <td key={subject.id} className="px-6 py-4 whitespace-nowrap text-center">
                          {isEditing ? (
                            <div className="flex items-center justify-center space-x-2">
                              <input
                                type="number"
                                value={mark}
                                onChange={(e) => handleMarkChange(student.rollNumber, subject.id, e.target.value)}
                                min="0"
                                max={subject.maxMarks}
                                className="w-20 px-2 py-1 border border-blue-500 rounded focus:ring-2 focus:ring-blue-500 text-center"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleSaveCell()
                                  if (e.key === 'Escape') handleCancelEdit()
                                }}
                              />
                              <button
                                onClick={handleSaveCell}
                                className="p-1 text-green-600 hover:bg-green-50 rounded"
                              >
                                <CheckIcon className="w-5 h-5" />
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="p-1 text-red-600 hover:bg-red-50 rounded"
                              >
                                <XMarkIcon className="w-5 h-5" />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleCellClick(student.rollNumber, subject.id)}
                              className="inline-flex items-center px-3 py-1 rounded hover:bg-blue-50 group transition-colors"
                              title="Click to open question-wise marks entry"
                            >
                              <span className="text-sm font-semibold mr-2">{mark}</span>
                              <ArrowTopRightOnSquareIcon className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </button>
                          )}
                        </td>
                      )
                    })}
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-bold text-gray-900">
                      {calculateTotal(student.rollNumber)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900">
                      {percentage}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`text-lg font-bold ${color}`}>
                        {grade}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> Click on any marks cell to open question-wise entry page.
            <br />
            <strong>Voice Tip:</strong> Use the microphone button to update marks via voice command!
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

export default MarksSheetPage
