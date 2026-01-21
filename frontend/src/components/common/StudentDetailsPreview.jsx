const StudentDetailsPreview = ({ data }) => {
  if (!data) return null

  const { student, marks_summary, attendance } = data

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-3">Student Information</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
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
            <span className="text-gray-600">Gender:</span>
            <span className="ml-2 font-medium">{student.gender}</span>
          </div>
          <div>
            <span className="text-gray-600">Date of Birth:</span>
            <span className="ml-2 font-medium">
              {new Date(student.dob).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Attendance Summary */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-3">Attendance</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {attendance.total_sessions}
            </div>
            <div className="text-gray-600">Total Sessions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {attendance.present_count}
            </div>
            <div className="text-gray-600">Present</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {attendance.percentage}%
            </div>
            <div className="text-gray-600">Attendance</div>
          </div>
        </div>
      </div>

      {/* Marks Summary */}
      {Object.keys(marks_summary).length > 0 ? (
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Marks Summary</h3>
          <div className="space-y-4">
            {Object.entries(marks_summary).map(([examType, data]) => (
              <div key={examType} className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold text-gray-800 mb-2">{examType}</h4>
                <div className="space-y-1 text-sm">
                  {data.marks.map((mark, index) => (
                    <div key={index} className="flex justify-between">
                      <span className="text-gray-600">{mark.subject}:</span>
                      <span className="font-medium">
                        {mark.marks_obtained}/{mark.max_marks} ({mark.percentage.toFixed(1)}%)
                      </span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-2 border-t">
                    <span className="font-semibold">Total:</span>
                    <span className="font-semibold">
                      {data.percentage.toFixed(1)}% - Grade {data.grade}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="border rounded-lg p-4 text-center text-gray-500">
          No marks recorded yet
        </div>
      )}
    </div>
  )
}

export default StudentDetailsPreview
