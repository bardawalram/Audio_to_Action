import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeftIcon,
  ChartBarIcon,
  AcademicCapIcon,
  UserGroupIcon,
  CalendarDaysIcon,
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'
import api from '../services/api'

const ReportsPage = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const tabFromUrl = searchParams.get('tab')
  const [activeTab, setActiveTab] = useState(tabFromUrl || 'overview')
  const [selectedClass, setSelectedClass] = useState('')
  const [selectedSection, setSelectedSection] = useState('')
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [classPerformance, setClassPerformance] = useState([])
  const [topPerformers, setTopPerformers] = useState([])
  const [attendanceStats, setAttendanceStats] = useState(null)

  const classes = Array.from({ length: 10 }, (_, i) => i + 1)
  const sections = ['A', 'B', 'C']

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'class', name: 'Class Reports', icon: UserGroupIcon },
    { id: 'student', name: 'Student Reports', icon: AcademicCapIcon },
    { id: 'attendance', name: 'Attendance', icon: CalendarDaysIcon },
  ]

  // Update activeTab when URL parameter changes (for voice navigation)
  useEffect(() => {
    if (tabFromUrl && ['overview', 'class', 'student', 'attendance'].includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [tabFromUrl])

  useEffect(() => {
    fetchOverviewData()
  }, [])

  useEffect(() => {
    if (selectedClass && selectedSection) {
      fetchClassReport()
    }
  }, [selectedClass, selectedSection])

  const fetchOverviewData = async () => {
    setLoading(true)
    try {
      const response = await api.get('/marks/reports/overview/')
      setReportData(response.data)
      setClassPerformance(response.data.class_performance || [])
      setTopPerformers(response.data.top_performers || [])
      setAttendanceStats(response.data.attendance_stats || null)
    } catch (error) {
      console.error('Failed to fetch overview data:', error)
      // Use mock data if API fails
      setReportData(getMockOverviewData())
      setClassPerformance(getMockClassPerformance())
      setTopPerformers(getMockTopPerformers())
      setAttendanceStats(getMockAttendanceStats())
    }
    setLoading(false)
  }

  const fetchClassReport = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/marks/reports/class/${selectedClass}/${selectedSection}/`)
      setReportData(response.data)
    } catch (error) {
      console.error('Failed to fetch class report:', error)
      setReportData(getMockClassReport())
    }
    setLoading(false)
  }

  // Mock data functions for demo
  const getMockOverviewData = () => ({
    total_students: 150,
    total_classes: 30,
    average_attendance: 87.5,
    average_marks: 72.3,
  })

  const getMockClassPerformance = () => [
    { class: '1A', average: 85, students: 5 },
    { class: '1B', average: 78, students: 5 },
    { class: '1C', average: 82, students: 5 },
    { class: '2A', average: 75, students: 5 },
    { class: '2B', average: 80, students: 5 },
    { class: '2C', average: 77, students: 5 },
    { class: '3A', average: 88, students: 5 },
    { class: '3B', average: 71, students: 5 },
  ]

  const getMockTopPerformers = () => [
    { name: 'Student1 1A', class: '1A', percentage: 95, rank: 1 },
    { name: 'Student3 3A', class: '3A', percentage: 92, rank: 2 },
    { name: 'Student2 1A', class: '1A', percentage: 90, rank: 3 },
    { name: 'Student1 2B', class: '2B', percentage: 88, rank: 4 },
    { name: 'Student4 1C', class: '1C', percentage: 87, rank: 5 },
  ]

  const getMockAttendanceStats = () => ({
    overall_percentage: 87.5,
    present_today: 142,
    absent_today: 8,
    trend: 'up',
    trend_value: 2.3,
  })

  const getMockClassReport = () => ({
    class_name: `${selectedClass}${selectedSection}`,
    total_students: 5,
    subjects: [
      { name: 'Mathematics', average: 78, highest: 100, lowest: 45 },
      { name: 'Hindi', average: 82, highest: 95, lowest: 55 },
      { name: 'English', average: 75, highest: 92, lowest: 48 },
      { name: 'Science', average: 80, highest: 98, lowest: 52 },
      { name: 'Social Studies', average: 77, highest: 90, lowest: 50 },
    ],
    grade_distribution: [
      { grade: 'A+', count: 1, percentage: 20 },
      { grade: 'A', count: 2, percentage: 40 },
      { grade: 'B+', count: 1, percentage: 20 },
      { grade: 'B', count: 1, percentage: 20 },
    ],
    students: [
      { roll: 1, name: 'Student1', total: 465, percentage: 93, grade: 'A+' },
      { roll: 2, name: 'Student2', total: 420, percentage: 84, grade: 'A' },
      { roll: 3, name: 'Student3', total: 385, percentage: 77, grade: 'B+' },
      { roll: 4, name: 'Student4', total: 410, percentage: 82, grade: 'A' },
      { roll: 5, name: 'Student5', total: 350, percentage: 70, grade: 'B' },
    ],
  })

  const getGradeColor = (grade) => {
    const colors = {
      'A+': 'bg-green-500',
      'A': 'bg-green-400',
      'B+': 'bg-blue-500',
      'B': 'bg-blue-400',
      'C+': 'bg-yellow-500',
      'C': 'bg-yellow-400',
      'D': 'bg-orange-500',
      'F': 'bg-red-500',
    }
    return colors[grade] || 'bg-gray-400'
  }

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Students</p>
              <p className="text-3xl font-bold text-gray-800">
                {reportData?.total_students || 150}
              </p>
            </div>
            <UserGroupIcon className="w-12 h-12 text-blue-500 opacity-50" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Average Marks</p>
              <p className="text-3xl font-bold text-gray-800">
                {reportData?.average_marks || 72.3}%
              </p>
            </div>
            <AcademicCapIcon className="w-12 h-12 text-purple-500 opacity-50" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Attendance Rate</p>
              <p className="text-3xl font-bold text-gray-800">
                {attendanceStats?.overall_percentage || 87.5}%
              </p>
            </div>
            <div className="flex items-center">
              {attendanceStats?.trend === 'up' ? (
                <ArrowTrendingUpIcon className="w-6 h-6 text-green-500 mr-1" />
              ) : (
                <ArrowTrendingDownIcon className="w-6 h-6 text-red-500 mr-1" />
              )}
              <span className={`text-sm ${attendanceStats?.trend === 'up' ? 'text-green-500' : 'text-red-500'}`}>
                {attendanceStats?.trend_value || 2.3}%
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Classes</p>
              <p className="text-3xl font-bold text-gray-800">
                {reportData?.total_classes || 30}
              </p>
            </div>
            <ChartBarIcon className="w-12 h-12 text-orange-500 opacity-50" />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Class Performance Chart */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Class Performance</h3>
          <div className="space-y-3">
            {classPerformance.slice(0, 8).map((item, idx) => (
              <div key={idx} className="flex items-center">
                <span className="w-12 text-sm font-medium text-gray-600">{item.class}</span>
                <div className="flex-1 mx-3">
                  <div className="h-6 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        item.average >= 80 ? 'bg-green-500' :
                        item.average >= 60 ? 'bg-blue-500' :
                        item.average >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${item.average}%` }}
                    />
                  </div>
                </div>
                <span className="w-12 text-sm font-bold text-gray-800">{item.average}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Performers */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Performers</h3>
          <div className="space-y-3">
            {topPerformers.map((student, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                    idx === 0 ? 'bg-yellow-500' :
                    idx === 1 ? 'bg-gray-400' :
                    idx === 2 ? 'bg-orange-400' : 'bg-blue-400'
                  }`}>
                    {student.rank}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{student.name}</p>
                    <p className="text-sm text-gray-500">Class {student.class}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-green-600">{student.percentage}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Today's Attendance Summary */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Today's Attendance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-4xl font-bold text-green-600">{attendanceStats?.present_today || 142}</p>
            <p className="text-sm text-gray-600">Students Present</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-4xl font-bold text-red-600">{attendanceStats?.absent_today || 8}</p>
            <p className="text-sm text-gray-600">Students Absent</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-4xl font-bold text-blue-600">{attendanceStats?.overall_percentage || 87.5}%</p>
            <p className="text-sm text-gray-600">Attendance Rate</p>
          </div>
        </div>
      </div>
    </div>
  )

  const renderClassTab = () => (
    <div className="space-y-6">
      {/* Class Selector */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Select Class</h3>
        <div className="flex flex-wrap gap-4">
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select Class</option>
            {classes.map((cls) => (
              <option key={cls} value={cls}>Class {cls}</option>
            ))}
          </select>
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select Section</option>
            {sections.map((sec) => (
              <option key={sec} value={sec}>Section {sec}</option>
            ))}
          </select>
          <button
            onClick={fetchClassReport}
            disabled={!selectedClass || !selectedSection}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Generate Report
          </button>
        </div>
      </div>

      {/* Class Report Content */}
      {selectedClass && selectedSection && reportData && (
        <>
          {/* Class Summary */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">
                Class {reportData.class_name} Performance Report
              </h3>
              <button
                onClick={() => window.print()}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <DocumentArrowDownIcon className="w-5 h-5" />
                <span>Export PDF</span>
              </button>
            </div>
            <p className="text-gray-600">Total Students: {reportData.total_students}</p>
          </div>

          {/* Subject-wise Performance */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Subject-wise Performance</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Subject</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Average</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Highest</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Lowest</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Distribution</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.subjects?.map((subject, idx) => (
                    <tr key={idx} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-800">{subject.name}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                          subject.average >= 80 ? 'bg-green-100 text-green-800' :
                          subject.average >= 60 ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {subject.average}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-green-600 font-medium">{subject.highest}</td>
                      <td className="px-4 py-3 text-center text-red-600 font-medium">{subject.lowest}</td>
                      <td className="px-4 py-3">
                        <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${subject.average}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Grade Distribution */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Grade Distribution</h3>
            <div className="flex flex-wrap gap-4 justify-center">
              {reportData.grade_distribution?.map((item, idx) => (
                <div key={idx} className="text-center">
                  <div className={`w-20 h-20 rounded-full ${getGradeColor(item.grade)} flex items-center justify-center text-white text-2xl font-bold mb-2`}>
                    {item.count}
                  </div>
                  <p className="font-semibold text-gray-800">{item.grade}</p>
                  <p className="text-sm text-gray-500">{item.percentage}%</p>
                </div>
              ))}
            </div>
          </div>

          {/* Student Rankings */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Student Rankings</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Rank</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Roll No</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Name</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Total</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Percentage</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Grade</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.students?.sort((a, b) => b.percentage - a.percentage).map((student, idx) => (
                    <tr key={idx} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                          idx === 0 ? 'bg-yellow-500' :
                          idx === 1 ? 'bg-gray-400' :
                          idx === 2 ? 'bg-orange-400' : 'bg-blue-400'
                        }`}>
                          {idx + 1}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-800">{student.roll}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">{student.name}</td>
                      <td className="px-4 py-3 text-center text-gray-800">{student.total}/500</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                          student.percentage >= 80 ? 'bg-green-100 text-green-800' :
                          student.percentage >= 60 ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {student.percentage}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-3 py-1 rounded-full text-white font-bold ${getGradeColor(student.grade)}`}>
                          {student.grade}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => alert(`Say: "Download progress report for roll ${student.roll}"`)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Download Report
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )

  const renderStudentTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Individual Student Report</h3>
        <p className="text-gray-600 mb-4">
          Use voice command to download individual student progress reports:
        </p>
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-blue-800 font-medium mb-2">Voice Commands:</p>
          <ul className="space-y-2 text-blue-700">
            <li>"Download progress report for roll 1"</li>
            <li>"Download report for student 5 class 1A"</li>
            <li>"Get progress report for roll 3"</li>
          </ul>
        </div>
      </div>

      {/* Quick Search */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Search</h3>
        <div className="flex flex-wrap gap-4">
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Class</option>
            {classes.map((cls) => (
              <option key={cls} value={cls}>Class {cls}</option>
            ))}
          </select>
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Section</option>
            {sections.map((sec) => (
              <option key={sec} value={sec}>Section {sec}</option>
            ))}
          </select>
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or roll number..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Student List with Quick Actions */}
      {selectedClass && selectedSection && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Students in Class {selectedClass}{selectedSection}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5].map((roll) => (
              <div
                key={roll}
                className="border rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer"
                onClick={() => alert(`Say: "Download progress report for roll ${roll}"`)}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-bold">{roll}</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">Student{roll} {selectedClass}{selectedSection}</p>
                    <p className="text-sm text-gray-500">Roll No: {roll}</p>
                  </div>
                </div>
                <div className="mt-3 flex justify-between text-sm">
                  <span className="text-gray-500">Click to download report</span>
                  <DocumentArrowDownIcon className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderAttendanceTab = () => (
    <div className="space-y-6">
      {/* Attendance Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border-t-4 border-green-500">
          <p className="text-sm text-gray-500">Present Today</p>
          <p className="text-3xl font-bold text-green-600">{attendanceStats?.present_today || 142}</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border-t-4 border-red-500">
          <p className="text-sm text-gray-500">Absent Today</p>
          <p className="text-3xl font-bold text-red-600">{attendanceStats?.absent_today || 8}</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border-t-4 border-blue-500">
          <p className="text-sm text-gray-500">Overall Rate</p>
          <p className="text-3xl font-bold text-blue-600">{attendanceStats?.overall_percentage || 87.5}%</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border-t-4 border-purple-500">
          <p className="text-sm text-gray-500">This Week</p>
          <div className="flex items-center">
            <p className="text-3xl font-bold text-purple-600">89%</p>
            <ArrowTrendingUpIcon className="w-6 h-6 text-green-500 ml-2" />
          </div>
        </div>
      </div>

      {/* Class-wise Attendance */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Class-wise Attendance Today</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {classPerformance.slice(0, 10).map((item, idx) => (
            <div key={idx} className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="font-semibold text-gray-800">{item.class}</p>
              <p className="text-2xl font-bold text-blue-600">
                {Math.floor(85 + Math.random() * 15)}%
              </p>
              <p className="text-xs text-gray-500">{item.students} students</p>
            </div>
          ))}
        </div>
      </div>

      {/* Weekly Trend */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Weekly Attendance Trend</h3>
        <div className="flex items-end justify-around h-48">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].map((day, idx) => {
            const height = 70 + Math.floor(Math.random() * 25)
            return (
              <div key={day} className="flex flex-col items-center">
                <div
                  className="w-12 bg-blue-500 rounded-t-lg transition-all hover:bg-blue-600"
                  style={{ height: `${height}%` }}
                />
                <p className="mt-2 text-sm text-gray-600">{day}</p>
                <p className="text-xs text-gray-500">{height}%</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Low Attendance Alert */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          <span className="w-3 h-3 bg-red-500 rounded-full mr-2 animate-pulse" />
          Low Attendance Alerts
        </h3>
        <div className="space-y-3">
          {[
            { name: 'Student3 2A', class: '2A', attendance: 65 },
            { name: 'Student5 1B', class: '1B', attendance: 70 },
            { name: 'Student2 3C', class: '3C', attendance: 72 },
          ].map((student, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-800">{student.name}</p>
                <p className="text-sm text-gray-500">Class {student.class}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-red-600">{student.attendance}%</p>
                <p className="text-xs text-red-500">Below 75% threshold</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
                <p className="text-gray-500">View performance insights and generate reports</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{tab.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        ) : (
          <>
            {activeTab === 'overview' && renderOverviewTab()}
            {activeTab === 'class' && renderClassTab()}
            {activeTab === 'student' && renderStudentTab()}
            {activeTab === 'attendance' && renderAttendanceTab()}
          </>
        )}
      </div>

      {/* Voice Button and Confirmation Dialog */}
      <FloatingVoiceButton />
      <ConfirmationDialog />
      <VoiceReceiptModal />
    </div>
  )
}

export default ReportsPage
