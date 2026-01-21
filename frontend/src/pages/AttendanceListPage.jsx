import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

const AttendanceListPage = () => {
  const navigate = useNavigate()
  const [classes, setClasses] = useState([])
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])

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
    navigate(`/attendance/${classData.class}/${classData.section}`, {
      state: { date: selectedDate }
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
                <h1 className="text-3xl font-bold text-gray-900">Attendance Management</h1>
                <p className="text-gray-500">Select a class to mark attendance</p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                max={new Date().toISOString().split('T')[0]}
                className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
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
                <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                  Class {classData.class}
                </div>
              </div>
              <p className="text-gray-600">Section {classData.section}</p>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  Click to view/mark attendance
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AttendanceListPage
