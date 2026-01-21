import React from 'react'

const BatchQuestionMarksPreview = ({ data }) => {
  const { student, subject, updates } = data || {}

  if (!student || !subject || !updates || updates.length === 0) {
    return <div className="text-red-600">Invalid batch update data</div>
  }

  // Calculate totals
  const oldTotal = updates.reduce((sum, u) => sum + (u.old_marks || 0), 0)
  const newTotal = updates.reduce((sum, u) => sum + u.marks_obtained, 0)

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-semibold text-gray-700 mb-2">Student Details</h3>
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
        <h3 className="font-semibold text-gray-700 px-4 py-3 bg-gray-50 border-b">
          Batch Question Marks Update ({updates.length} questions)
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
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Question {update.question_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                    {update.old_marks || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-bold text-green-600">
                    {update.marks_obtained}
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
