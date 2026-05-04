import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeftIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'

const AttendanceSheetPage = () => {
  const { classNum, section } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [students, setStudents] = useState([])
  const [attendance, setAttendance] = useState({})
  const [date, setDate] = useState(location.state?.date || new Date().toISOString().split('T')[0])
  const [saved, setSaved] = useState(false)

  const storageKey = `attendance_${classNum}${section}_${date}`

  useEffect(() => {
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

    // Load saved attendance from localStorage, or initialize as ABSENT
    const savedData = localStorage.getItem(storageKey)
    if (savedData) {
      try {
        setAttendance(JSON.parse(savedData))
      } catch {
        const initialAttendance = {}
        studentList.forEach(student => {
          initialAttendance[student.id] = 'ABSENT'
        })
        setAttendance(initialAttendance)
      }
    } else {
      const initialAttendance = {}
      studentList.forEach(student => {
        initialAttendance[student.id] = 'ABSENT'
      })
      setAttendance(initialAttendance)
    }
  }, [classNum, section, date, storageKey])

  // Listen for voice command attendance updates
  useEffect(() => {
    const handleAttendanceUpdate = (event) => {
      const { status, excludedRolls, markedCount } = event.detail
      console.log('[AttendanceSheetPage] Voice command attendance update:', event.detail)

      // Update all students based on voice command
      const newAttendance = {}
      students.forEach(student => {
        const isExcluded = excludedRolls && excludedRolls.includes(student.rollNumber)
        newAttendance[student.id] = isExcluded ? (status === 'PRESENT' ? 'ABSENT' : 'PRESENT') : status
      })
      setAttendance(newAttendance)

      // Auto-save
      localStorage.setItem(storageKey, JSON.stringify(newAttendance))
      setSaved(true)
      console.log(`[AttendanceSheetPage] Updated ${markedCount} students to ${status}`)
    }

    window.addEventListener('attendanceUpdated', handleAttendanceUpdate)
    return () => window.removeEventListener('attendanceUpdated', handleAttendanceUpdate)
  }, [students, storageKey])

  // Listen for storage changes (from other tabs or voice commands)
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === storageKey && e.newValue) {
        try {
          setAttendance(JSON.parse(e.newValue))
        } catch { /* ignore */ }
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [storageKey])

  const toggleAttendance = (studentId) => {
    setAttendance(prev => {
      const updated = {
        ...prev,
        [studentId]: prev[studentId] === 'PRESENT' ? 'ABSENT' : 'PRESENT'
      }
      localStorage.setItem(storageKey, JSON.stringify(updated))
      return updated
    })
    setSaved(false)
  }

  const markAllPresent = () => {
    const newAttendance = {}
    students.forEach(student => {
      newAttendance[student.id] = 'PRESENT'
    })
    setAttendance(newAttendance)
    localStorage.setItem(storageKey, JSON.stringify(newAttendance))
    setSaved(false)
  }

  const markAllAbsent = () => {
    const newAttendance = {}
    students.forEach(student => {
      newAttendance[student.id] = 'ABSENT'
    })
    setAttendance(newAttendance)
    localStorage.setItem(storageKey, JSON.stringify(newAttendance))
    setSaved(false)
  }

  const saveAttendance = () => {
    localStorage.setItem(storageKey, JSON.stringify(attendance))
    console.log('Saving attendance:', {
      class: classNum,
      section,
      date,
      records: attendance
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const presentCount = Object.values(attendance).filter(status => status === 'PRESENT').length
  const absentCount = students.length - presentCount

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/attendance')}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Attendance - Class {classNum}{section}
                </h1>
                <p className="text-gray-500">Mark attendance for all students</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                  className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={markAllPresent}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Mark All Present
                </button>
                <button
                  onClick={markAllAbsent}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  Mark All Absent
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <div className="text-center">
                <p className="text-sm text-gray-600">Present</p>
                <p className="text-2xl font-bold text-green-600">{presentCount}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Absent</p>
                <p className="text-2xl font-bold text-red-600">{absentCount}</p>
              </div>
              <button
                onClick={saveAttendance}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
              >
                Save Attendance
              </button>
            </div>
          </div>
          {saved && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3 text-green-800">
              Attendance saved successfully!
            </div>
          )}
        </div>

        {/* Student List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Roll Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Student Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Class
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Attendance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {student.rollNumber}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {student.className}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => toggleAttendance(student.id)}
                      className={`inline-flex items-center px-4 py-2 rounded-lg font-semibold transition-colors ${
                        attendance[student.id] === 'PRESENT'
                          ? 'bg-green-100 text-green-800 hover:bg-green-200'
                          : 'bg-red-100 text-red-800 hover:bg-red-200'
                      }`}
                    >
                      {attendance[student.id] === 'PRESENT' ? (
                        <>
                          <CheckCircleIcon className="w-5 h-5 mr-2" />
                          Present
                        </>
                      ) : (
                        <>
                          <XCircleIcon className="w-5 h-5 mr-2" />
                          Absent
                        </>
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> Click on status buttons to toggle attendance between Present and Absent.
            <br />
            <strong>Voice Tip:</strong> Use the microphone button to mark attendance via voice command!
          </p>
        </div>
      </div>

      {/* Floating Voice Button */}
      <FloatingVoiceButton
        voiceContext={{
          context_class: classNum,
          context_section: section
        }}
      />

      {/* Confirmation Dialog */}
      <ConfirmationDialog />
      <VoiceReceiptModal />
    </div>
  )
}

export default AttendanceSheetPage
