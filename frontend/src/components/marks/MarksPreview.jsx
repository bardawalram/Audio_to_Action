const MarksPreview = ({ data }) => {
  if (!data) return null

  const { student, exam_type, marks_table, total_subjects } = data

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Student Information</h3>
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
            <span className="ml-2 font-medium">{exam_type.name}</span>
          </div>
        </div>
      </div>

      {/* Marks Table */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-3">
          Marks to be entered ({total_subjects} subjects):
        </h3>
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subject
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Marks Obtained
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max Marks
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Percentage
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {marks_table.map((mark, index) => {
                const percentage = (mark.marks_obtained / mark.max_marks) * 100
                return (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {mark.subject}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {mark.marks_obtained}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {mark.max_marks}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {percentage.toFixed(1)}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          Please verify the marks carefully before confirming. This action will
          create or update marks records.
        </p>
      </div>
    </div>
  )
}

export default MarksPreview
