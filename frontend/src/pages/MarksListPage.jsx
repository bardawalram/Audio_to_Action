import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'

const MarksListPage = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [classes, setClasses] = useState([])

  // Get exam type from URL query parameter or default to UNIT_TEST
  const examTypeFromUrl = searchParams.get('examType')
  const [selectedExamType, setSelectedExamType] = useState(
    examTypeFromUrl && ['UNIT_TEST', 'MIDTERM', 'FINAL'].includes(examTypeFromUrl)
      ? examTypeFromUrl
      : 'UNIT_TEST'
  )

  const examTypes = [
    { value: 'UNIT_TEST', label: 'Unit Test' },
    { value: 'MIDTERM', label: 'Midterm Exam' },
    { value: 'FINAL', label: 'Final Exam' }
  ]

  // Sync exam type with URL parameter when it changes (e.g., via voice command)
  useEffect(() => {
    if (examTypeFromUrl && ['UNIT_TEST', 'MIDTERM', 'FINAL'].includes(examTypeFromUrl)) {
      setSelectedExamType(examTypeFromUrl)
    }
  }, [examTypeFromUrl])

  useEffect(() => {
    // Generate class list (1-10) with sections (A, B, C)
    const classList = []
    for (let i = 1; i <= 10; i++) {
      ['A', 'B', 'C'].forEach(section => {
        classList.push({
          id: `${i}${section}`,
          class: i,
          section: section,
          name: `Class ${i}${getOrdinalSuffix(i)} - Section ${section}`
        })
      })
    }
    setClasses(classList)
  }, [])

  const getOrdinalSuffix = (num) => {
    const suffixes = ['th', 'st', 'nd', 'rd']
    const value = num % 100
    return suffixes[(value - 20) % 10] || suffixes[value] || suffixes[0]
  }

  const handleClassClick = (classData) => {
    navigate(`/marks/${classData.class}/${classData.section}`, {
      state: { examType: selectedExamType }
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Marks Management</h1>
                <p className="text-gray-500">Select a class or use voice: "Open class 1A marks"</p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Exam Type
              </label>
              <select
                value={selectedExamType}
                onChange={(e) => setSelectedExamType(e.target.value)}
                className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {examTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Class Grid */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classes.map((classData) => (
            <button
              key={classData.id}
              onClick={() => handleClassClick(classData)}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 text-left border-2 border-transparent hover:border-blue-500"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-bold text-gray-900">
                  {classData.class}{getOrdinalSuffix(classData.class)} {classData.section}
                </h3>
                <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-semibold">
                  Class {classData.class}
                </div>
              </div>
              <p className="text-gray-600">Section {classData.section}</p>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  Click to view/update marks
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Voice Button and Confirmation Dialog */}
      <FloatingVoiceButton />
      <ConfirmationDialog />
      <VoiceReceiptModal />
    </div>
  )
}

export default MarksListPage
