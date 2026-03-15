import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  ArrowLeftIcon,
  AcademicCapIcon,
  CurrencyRupeeIcon,
} from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'
import feeService from '../services/feeService'

const FeeListPage = () => {
  const navigate = useNavigate()
  const { user } = useSelector((state) => state.auth)
  const [classData, setClassData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, high, medium, low

  useEffect(() => {
    fetchClassData()
  }, [])

  const fetchClassData = async () => {
    try {
      setLoading(true)
      const response = await feeService.getClassWiseReport()
      const data = response.data?.classes || response.data || []
      setClassData(data)
    } catch (err) {
      console.error('Error fetching class data:', err)
      // Fallback data for display
      const fallback = []
      for (let i = 1; i <= 10; i++) {
        fallback.push({
          class_name: i > 3 ? `${i}th` : i === 1 ? '1st' : i === 2 ? '2nd' : '3rd',
          grade_number: i,
          student_count: 60,
          expected: 0,
          collected: 0,
          percentage: 0,
        })
      }
      setClassData(fallback)
    } finally {
      setLoading(false)
    }
  }

  const sections = ['A', 'B', 'C']

  const getPercentageColor = (pct) => {
    if (pct >= 80) return { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300', bar: 'bg-green-500' }
    if (pct >= 50) return { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', bar: 'bg-yellow-500' }
    return { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', bar: 'bg-red-500' }
  }

  const filteredData = classData.filter((cls) => {
    if (filter === 'all') return true
    if (filter === 'high') return cls.percentage >= 80
    if (filter === 'medium') return cls.percentage >= 50 && cls.percentage < 80
    if (filter === 'low') return cls.percentage < 50
    return true
  })

  const formatINR = (amt) => Number(amt).toLocaleString('en-IN')

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center space-x-2 text-emerald-100 text-sm">
                <Link to="/dashboard" className="hover:text-white">Dashboard</Link>
                <span>/</span>
                <span className="text-white font-medium">Fee Collection</span>
              </div>
              <h1 className="text-2xl font-bold">Fee Collection</h1>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <CurrencyRupeeIcon className="w-8 h-8 text-emerald-200" />
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Filter Bar */}
        <div className="mb-6 flex items-center justify-between">
          <p className="text-gray-600">
            Select a class and section to manage fee collection
          </p>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">Filter:</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            >
              <option value="all">All Classes</option>
              <option value="high">High Collection (80%+)</option>
              <option value="medium">Medium (50-80%)</option>
              <option value="low">Low (&lt;50%)</option>
            </select>
          </div>
        </div>

        {/* Class Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading class data...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredData.map((cls) => {
              const colors = getPercentageColor(cls.percentage)
              return (
                <div
                  key={cls.grade_number}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
                >
                  {/* Card Header */}
                  <div className="px-5 py-4 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="bg-emerald-100 p-2 rounded-lg">
                          <AcademicCapIcon className="w-6 h-6 text-emerald-600" />
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-900 text-lg">
                            Class {cls.class_name}
                          </h3>
                          <p className="text-xs text-gray-500">
                            {cls.student_count} students
                          </p>
                        </div>
                      </div>
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-bold ${colors.bg} ${colors.text}`}
                      >
                        {cls.percentage}%
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${colors.bar} transition-all duration-500`}
                        style={{ width: `${Math.min(100, cls.percentage)}%` }}
                      ></div>
                    </div>

                    {cls.expected > 0 && (
                      <div className="mt-2 flex justify-between text-xs text-gray-500">
                        <span>Rs. {formatINR(cls.collected)}</span>
                        <span>Rs. {formatINR(cls.expected)}</span>
                      </div>
                    )}
                  </div>

                  {/* Section Buttons */}
                  <div className="px-5 py-3">
                    <p className="text-xs text-gray-500 mb-2">Select Section</p>
                    <div className="flex space-x-2">
                      {sections.map((section) => (
                        <button
                          key={section}
                          onClick={() => navigate(`/fees/${cls.grade_number}/${section}`)}
                          className="flex-1 px-4 py-2.5 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 hover:text-emerald-800 transition-colors font-semibold text-sm border border-emerald-200"
                        >
                          {section}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {filteredData.length === 0 && !loading && (
          <div className="text-center py-12">
            <p className="text-gray-500">No classes match the selected filter.</p>
          </div>
        )}
      </div>

      {/* Voice Components */}
      <FloatingVoiceButton />
      <ConfirmationDialog />
      <VoiceReceiptModal />
    </div>
  )
}

export default FeeListPage
