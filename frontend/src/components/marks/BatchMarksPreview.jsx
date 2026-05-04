import { useState, useEffect } from 'react'
import { PencilIcon, CheckIcon } from '@heroicons/react/24/outline'

const BatchMarksPreview = ({ data, onUpdate }) => {
  const { students: initialStudents } = data || {}
  const [studentsData, setStudentsData] = useState(initialStudents || [])
  const [editingIndex, setEditingIndex] = useState(null)

  useEffect(() => {
    if (initialStudents) {
      setStudentsData(initialStudents)
    }
  }, [initialStudents])

  if (!data || !studentsData.length) return null

  const handleMarksChange = (studentIdx, markIdx, newValue) => {
    const value = parseInt(newValue) || 0
    const maxMarks = studentsData[studentIdx].marks_table[markIdx].max_marks || 100
    const clampedValue = Math.min(Math.max(0, value), maxMarks)

    const updated = studentsData.map((s, si) => {
      if (si !== studentIdx) return s
      const newMarksTable = s.marks_table.map((m, mi) =>
        mi === markIdx ? { ...m, marks_obtained: clampedValue } : m
      )
      return { ...s, marks_table: newMarksTable }
    })
    setStudentsData(updated)

    if (onUpdate) {
      onUpdate({ ...data, students: updated })
    }
  }

  const validStudents = studentsData.filter(s => s.student && !s.error)
  const errorStudents = studentsData.filter(s => s.error)

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 rounded-lg p-3">
        <h3 className="font-semibold text-blue-900 text-lg">
          Batch Update: {validStudents.length} Students
        </h3>
      </div>

      {validStudents.map((studentData, studentIdx) => {
        const { student, exam_type, marks_table = [] } = studentData
        const isEditing = editingIndex === studentIdx
        const totalObtained = marks_table.reduce((sum, m) => sum + m.marks_obtained, 0)
        const totalMax = marks_table.reduce((sum, m) => sum + m.max_marks, 0)
        const overallPercentage = totalMax > 0 ? (totalObtained / totalMax) * 100 : 0

        // Find actual index in studentsData for marks change handler
        const actualIdx = studentsData.indexOf(studentData)

        return (
          <div key={studentIdx} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* Student Header */}
            <div className="bg-blue-50 p-3 flex justify-between items-center">
              <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm flex-1">
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium">{student.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Roll Number:</span>
                  <span className="ml-2 font-medium">{student.roll_number}</span>
                </div>
                <div>
                  <span className="text-gray-600">Class:</span>
                  <span className="ml-2 font-medium">{student.class}</span>
                </div>
                <div>
                  <span className="text-gray-600">Exam Type:</span>
                  <span className="ml-2 font-medium">{exam_type?.name}</span>
                </div>
              </div>
              <button
                onClick={() => setEditingIndex(isEditing ? null : studentIdx)}
                className={`px-3 py-1 rounded-md text-sm flex items-center space-x-1 transition-colors ${
                  isEditing
                    ? 'bg-green-100 text-green-700 hover:bg-green-200'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                {isEditing ? (
                  <><CheckIcon className="w-4 h-4" /><span>Done</span></>
                ) : (
                  <><PencilIcon className="w-4 h-4" /><span>Edit</span></>
                )}
              </button>
            </div>

            {/* Marks Table */}
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Marks</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Max</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">%</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {marks_table.map((mark, markIdx) => {
                  const pct = (mark.marks_obtained / mark.max_marks) * 100
                  return (
                    <tr key={markIdx} className={isEditing ? 'bg-yellow-50' : ''}>
                      <td className="px-4 py-2 text-sm font-medium text-gray-900">{mark.subject}</td>
                      <td className="px-4 py-2 text-center text-sm">
                        {isEditing ? (
                          <input
                            type="number"
                            min="0"
                            max={mark.max_marks}
                            value={mark.marks_obtained}
                            onChange={(e) => handleMarksChange(actualIdx, markIdx, e.target.value)}
                            className="w-16 text-center font-bold text-green-600 border-2 border-green-300 rounded px-1 py-0.5 focus:border-green-500 focus:ring-1 focus:ring-green-500"
                          />
                        ) : (
                          <span className="font-bold text-green-600">{mark.marks_obtained}</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-center text-sm text-gray-500">{mark.max_marks}</td>
                      <td className="px-4 py-2 text-center text-sm">
                        <span className={pct >= 60 ? 'text-green-600' : pct >= 40 ? 'text-yellow-600' : 'text-red-600'}>
                          {pct.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot className="bg-blue-50">
                <tr className="font-bold">
                  <td className="px-4 py-2 text-sm text-gray-900">TOTAL</td>
                  <td className="px-4 py-2 text-center text-sm text-green-700">{totalObtained}</td>
                  <td className="px-4 py-2 text-center text-sm text-gray-700">{totalMax}</td>
                  <td className="px-4 py-2 text-center text-sm">
                    <span className={overallPercentage >= 60 ? 'text-green-700' : overallPercentage >= 40 ? 'text-yellow-700' : 'text-red-700'}>
                      {overallPercentage.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )
      })}

      {errorStudents.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-800 font-medium">Could not find:</p>
          {errorStudents.map((s, i) => (
            <p key={i} className="text-sm text-red-600">Roll {s.roll_number}: {s.error}</p>
          ))}
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          Please verify marks for all {validStudents.length} students before confirming.
        </p>
      </div>
    </div>
  )
}

export default BatchMarksPreview
