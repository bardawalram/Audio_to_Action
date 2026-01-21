const AttendancePreview = ({ data }) => {
  if (!data) return null

  const { class_section, date, student_count, mark_all, status, already_marked, action } = data

  return (
    <div className="space-y-4">
      {/* Class Info */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Attendance Details</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-600">Class:</span>
            <span className="ml-2 font-medium">{class_section.name}</span>
          </div>
          <div>
            <span className="text-gray-600">Date:</span>
            <span className="ml-2 font-medium">{new Date(date).toLocaleDateString()}</span>
          </div>
          <div>
            <span className="text-gray-600">Total Students:</span>
            <span className="ml-2 font-medium">{student_count}</span>
          </div>
          <div>
            <span className="text-gray-600">Status:</span>
            <span className="ml-2 font-medium">{status}</span>
          </div>
        </div>
      </div>

      {/* Attendance Summary */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-3">Action to be performed:</h3>
        <div className="space-y-2 text-sm">
          {mark_all && (
            <p className="text-gray-700">
              All <span className="font-semibold">{student_count} students</span> in class{' '}
              <span className="font-semibold">{class_section.name}</span> will be marked as{' '}
              <span className="font-semibold text-green-600">{status}</span>.
            </p>
          )}

          {already_marked && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
              <p className="text-yellow-800 text-sm">
                Attendance has already been marked for this class today. This will{' '}
                <span className="font-semibold">update</span> the existing records.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          Please confirm before marking attendance. This action will {action === 'update' ? 'update' : 'create'} attendance records for {student_count} students.
        </p>
      </div>
    </div>
  )
}

export default AttendancePreview
