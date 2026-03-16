import { useState, useEffect } from 'react'
import { PencilIcon, CheckIcon } from '@heroicons/react/24/outline'

const SingleStudentPreview = ({ data, onUpdate, studentIndex }) => {
  const { student, exam_type, marks_table: initialMarks, total_subjects } = data || {}
  const [marksTable, setMarksTable] = useState(initialMarks || [])
  const [isEditing, setIsEditing] = useState(false)

  // Sync marks when data changes
  useEffect(() => {
    if (initialMarks) {
      setMarksTable(initialMarks)
    }
  }, [initialMarks])

  if (!data || !student) return null

  const handleMarksChange = (index, newValue) => {
    const value = parseInt(newValue) || 0
    const maxMarks = marksTable[index].max_marks || 100
    const clampedValue = Math.min(Math.max(0, value), maxMarks)

    const newMarksTable = [...marksTable]
    newMarksTable[index] = {
      ...newMarksTable[index],
      marks_obtained: clampedValue
    }
    setMarksTable(newMarksTable)

    // Notify parent of the change
    if (onUpdate) {
      onUpdate({ ...data, marks_table: newMarksTable })
    }
  }

  const toggleEdit = () => {
    setIsEditing(!isEditing)
  }

  // Calculate total
  const totalObtained = marksTable.reduce((sum, m) => sum + m.marks_obtained, 0)
  const totalMax = marksTable.reduce((sum, m) => sum + m.max_marks, 0)
  const overallPercentage = totalMax > 0 ? (totalObtained / totalMax) * 100 : 0

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-blue-900">Student Information</h3>
          <button
            onClick={toggleEdit}
            className={`px-3 py-1 rounded-md text-sm flex items-center space-x-1 transition-colors ${
              isEditing
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
          >
            {isEditing ? (
              <>
                <CheckIcon className="w-4 h-4" />
                <span>Done</span>
              </>
            ) : (
              <>
                <PencilIcon className="w-4 h-4" />
                <span>Edit Marks</span>
              </>
            )}
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
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
      </div>

      {/* Marks Table */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-3 flex items-center justify-between">
          <span>Marks to be entered ({total_subjects} subjects):</span>
          {isEditing && (
            <span className="text-xs text-blue-600 font-normal">Click on marks to edit</span>
          )}
        </h3>
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subject
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Marks Obtained
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max Marks
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Percentage
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {marksTable.map((mark, index) => {
                const percentage = (mark.marks_obtained / mark.max_marks) * 100
                return (
                  <tr key={index} className={isEditing ? 'bg-yellow-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {mark.subject}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                      {isEditing ? (
                        <input
                          type="number"
                          min="0"
                          max={mark.max_marks}
                          value={mark.marks_obtained}
                          onChange={(e) => handleMarksChange(index, e.target.value)}
                          className="w-20 text-center font-bold text-green-600 border-2 border-green-300 rounded px-2 py-1 focus:border-green-500 focus:ring-1 focus:ring-green-500"
                        />
                      ) : (
                        <span className="font-bold text-green-600">{mark.marks_obtained}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                      {mark.max_marks}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                      <span className={percentage >= 60 ? 'text-green-600' : percentage >= 40 ? 'text-yellow-600' : 'text-red-600'}>
                        {percentage.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
            {/* Total Row */}
            <tfoot className="bg-blue-50">
              <tr className="font-bold">
                <td className="px-6 py-3 text-sm text-gray-900">TOTAL</td>
                <td className="px-6 py-3 text-center text-sm text-green-700">{totalObtained}</td>
                <td className="px-6 py-3 text-center text-sm text-gray-700">{totalMax}</td>
                <td className="px-6 py-3 text-center text-sm">
                  <span className={overallPercentage >= 60 ? 'text-green-700' : overallPercentage >= 40 ? 'text-yellow-700' : 'text-red-700'}>
                    {overallPercentage.toFixed(1)}%
                  </span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          {isEditing ? (
            <>Click <strong>Done</strong> when finished editing, then <strong>Confirm</strong> to save.</>
          ) : (
            <>Please verify the marks carefully before confirming. Click <strong>Edit Marks</strong> to make changes.</>
          )}
        </p>
      </div>
    </div>
  )
}

const MarksPreview = ({ data, onUpdate }) => {
  if (!data) return null

  // Multi-student mode
  if (data.multi_student && data.students_data) {
    return (
      <div className="space-y-6">
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
          <p className="text-sm font-semibold text-indigo-800">
            Updating marks for {data.total_students} students
          </p>
        </div>
        {data.students_data.map((studentData, index) => (
          <div key={index} className="border-b border-gray-200 pb-4 last:border-0">
            <SingleStudentPreview
              data={studentData}
              studentIndex={index}
              onUpdate={(updatedStudentData) => {
                if (onUpdate) {
                  const newStudentsData = [...data.students_data]
                  newStudentsData[index] = updatedStudentData
                  onUpdate({ ...data, students_data: newStudentsData })
                }
              }}
            />
          </div>
        ))}
      </div>
    )
  }

  // Single student mode
  return <SingleStudentPreview data={data} onUpdate={onUpdate} />
}

export default MarksPreview
