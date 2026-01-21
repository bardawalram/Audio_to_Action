import React from 'react'

const QuestionMarksPreview = ({ data }) => {
  const { student, subject, question } = data || {}

  if (!student || !subject || !question) {
    return <div className="text-red-600">Invalid question marks data</div>
  }

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

      {/* Question Marks Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <h3 className="font-semibold text-gray-700 px-4 py-3 bg-gray-50 border-b">
          Question Marks Update
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
            </tr>
          </thead>
          <tbody className="bg-white">
            <tr className="bg-green-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                Question {question.number}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                {question.old_marks || 0}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-bold text-green-600">
                {question.marks_obtained}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                {question.max_marks}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <p className="text-sm text-blue-800">
          <strong>Action:</strong> Update Question {question.number} marks from{' '}
          <span className="font-semibold">{question.old_marks || 0}</span> to{' '}
          <span className="font-semibold text-green-600">{question.marks_obtained}</span> for{' '}
          {student.name} (Roll {student.roll_number}) in {subject.name}.
        </p>
      </div>
    </div>
  )
}

export default QuestionMarksPreview
