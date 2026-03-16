import React, { useState, useEffect } from 'react'
import { PencilIcon, CheckIcon } from '@heroicons/react/24/outline'

const BatchQuestionMarksPreview = ({ data, onUpdate }) => {
  const { student, subject, updates: initialUpdates } = data || {}
  const [updates, setUpdates] = useState(initialUpdates || [])
  const [isEditing, setIsEditing] = useState(false)

  // Sync updates when data changes
  useEffect(() => {
    if (initialUpdates) {
      setUpdates(initialUpdates)
    }
  }, [initialUpdates])

  if (!student || !subject || !updates || updates.length === 0) {
    return <div className="text-red-600">Invalid batch update data</div>
  }

  // Calculate totals
  const oldTotal = updates.reduce((sum, u) => sum + (u.old_marks || 0), 0)
  const newTotal = updates.reduce((sum, u) => sum + u.marks_obtained, 0)

  const handleMarksChange = (index, newValue) => {
    const value = parseFloat(newValue) || 0
    const maxMarks = updates[index].max_marks || 100
    const clampedValue = Math.min(Math.max(0, value), maxMarks)

    const newUpdates = [...updates]
    newUpdates[index] = {
      ...newUpdates[index],
      marks_obtained: clampedValue
    }
    setUpdates(newUpdates)

    // Notify parent of the change
    if (onUpdate) {
      onUpdate({ ...data, updates: newUpdates })
    }
  }

  const toggleEdit = () => {
    setIsEditing(!isEditing)
  }

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-700">Student Details</h3>
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
            <span className="text-gray-600">Subject:</span>
            <span className="ml-2 font-medium">{subject.name}</span>
          </div>
        </div>
      </div>

      {/* Batch Updates Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <h3 className="font-semibold text-gray-700 px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
          <span>Batch Question Marks Update ({updates.length} questions)</span>
          {isEditing && (
            <span className="text-xs text-blue-600 font-normal">Click on marks to edit</span>
          )}
        </h3>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Question
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Old Marks
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                New Marks
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Max Marks
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Change
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {updates.map((update, index) => {
              const change = update.marks_obtained - (update.old_marks || 0)
              const isIncrease = change > 0
              const isDecrease = change < 0

              return (
                <tr key={index} className={`hover:bg-gray-50 ${isEditing ? 'bg-yellow-50' : ''}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Question {update.question_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                    {update.old_marks || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                    {isEditing ? (
                      <input
                        type="number"
                        min="0"
                        max={update.max_marks || 100}
                        step="0.5"
                        value={update.marks_obtained}
                        onChange={(e) => handleMarksChange(index, e.target.value)}
                        className="w-16 text-center font-bold text-green-600 border-2 border-green-300 rounded px-2 py-1 focus:border-green-500 focus:ring-1 focus:ring-green-500"
                      />
                    ) : (
                      <span className="font-bold text-green-600">{update.marks_obtained}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                    {update.max_marks}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                    {change === 0 ? (
                      <span className="text-gray-400">No change</span>
                    ) : (
                      <span className={isIncrease ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                        {isIncrease ? '+' : ''}{change.toFixed(1)}
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
          {/* Total Row */}
          <tfoot className="bg-blue-50">
            <tr className="font-bold">
              <td className="px-6 py-3 text-sm text-gray-900">TOTAL</td>
              <td className="px-6 py-3 text-center text-sm text-gray-700">{oldTotal.toFixed(1)}</td>
              <td className="px-6 py-3 text-center text-sm text-green-700">{newTotal.toFixed(1)}</td>
              <td className="px-6 py-3 text-center text-sm text-gray-500">-</td>
              <td className="px-6 py-3 text-center text-sm">
                {newTotal - oldTotal > 0 ? (
                  <span className="text-green-700">+{(newTotal - oldTotal).toFixed(1)}</span>
                ) : newTotal - oldTotal < 0 ? (
                  <span className="text-red-700">{(newTotal - oldTotal).toFixed(1)}</span>
                ) : (
                  <span className="text-gray-500">0</span>
                )}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Summary */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <p className="text-sm text-blue-800">
          <strong>Action:</strong> Update {updates.length} questions for {student.name} (Roll {student.roll_number}) in {subject.name}.
          Total will change from <span className="font-semibold">{oldTotal.toFixed(1)}</span> to{' '}
          <span className="font-semibold text-green-600">{newTotal.toFixed(1)}</span> marks.
        </p>
      </div>
    </div>
  )
}

export default BatchQuestionMarksPreview
