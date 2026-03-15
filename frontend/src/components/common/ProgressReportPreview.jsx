import { DocumentArrowDownIcon, UserIcon, AcademicCapIcon, CalendarIcon } from '@heroicons/react/24/outline'

const ProgressReportPreview = ({ data }) => {
  if (!data) return null

  const { student, marks_summary, attendance, message } = data

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center space-x-3 text-blue-600">
        <DocumentArrowDownIcon className="w-8 h-8" />
        <div>
          <h3 className="font-semibold text-lg">Download Progress Report</h3>
          <p className="text-sm text-gray-600">{message}</p>
        </div>
      </div>

      {/* Student Info */}
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <UserIcon className="w-5 h-5 text-blue-600" />
          <h4 className="font-semibold text-gray-800">Student Information</h4>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Name:</span>
            <span className="ml-2 font-medium text-gray-800">{student?.name || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-500">Roll Number:</span>
            <span className="ml-2 font-medium text-gray-800">{student?.roll_number || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-500">Class:</span>
            <span className="ml-2 font-medium text-gray-800">{student?.class_name || `${student?.class}${student?.section}` || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Marks Summary */}
      {marks_summary && (
        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <AcademicCapIcon className="w-5 h-5 text-green-600" />
            <h4 className="font-semibold text-gray-800">Marks Summary</h4>
          </div>
          {marks_summary.subjects && marks_summary.subjects.length > 0 ? (
            <div className="space-y-2">
              {marks_summary.subjects.map((subject, idx) => (
                <div key={idx} className="flex justify-between text-sm">
                  <span className="text-gray-600">{subject.name}</span>
                  <span className="font-medium text-gray-800">
                    {subject.marks_obtained}/{subject.max_marks}
                  </span>
                </div>
              ))}
              <div className="border-t pt-2 mt-2 flex justify-between font-semibold">
                <span>Total</span>
                <span>{marks_summary.total_obtained}/{marks_summary.total_max} ({marks_summary.percentage}%)</span>
              </div>
              {marks_summary.grade && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Grade</span>
                  <span className="font-bold text-blue-600">{marks_summary.grade}</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No marks data available</p>
          )}
        </div>
      )}

      {/* Attendance Summary */}
      {attendance && (
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <CalendarIcon className="w-5 h-5 text-purple-600" />
            <h4 className="font-semibold text-gray-800">Attendance</h4>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{attendance.present_count || 0}</div>
              <div className="text-gray-500">Present</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{attendance.total_sessions || 0}</div>
              <div className="text-gray-500">Total Days</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{attendance.percentage || 0}%</div>
              <div className="text-gray-500">Attendance</div>
            </div>
          </div>
        </div>
      )}

      {/* Download Info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          <span className="font-semibold">Note:</span> Clicking confirm will download the progress report as a PDF file.
        </p>
      </div>
    </div>
  )
}

export default ProgressReportPreview
