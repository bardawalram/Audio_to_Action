import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import {
  ArrowRightOnRectangleIcon,
  CurrencyRupeeIcon,
  BanknotesIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
} from '@heroicons/react/24/solid'
import {
  ArrowTrendingUpIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'
import feeService from '../services/feeService'
import { setDashboard, setLoading, setError } from '../store/slices/feeSlice'
import { logout } from '../store/slices/authSlice'

const AccountantDashboardPage = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { user } = useSelector((state) => state.auth)
  const { dashboard, loading } = useSelector((state) => state.fee)

  const [recentTransactions, setRecentTransactions] = useState([])
  const [classWiseProgress, setClassWiseProgress] = useState([])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  // Refresh dashboard when fee is collected via voice command
  useEffect(() => {
    const handleFeeCollected = () => {
      console.log('Fee collected via voice — refreshing dashboard')
      fetchDashboardData()
    }
    window.addEventListener('feeCollected', handleFeeCollected)
    return () => window.removeEventListener('feeCollected', handleFeeCollected)
  }, [])

  const fetchDashboardData = async () => {
    try {
      dispatch(setLoading(true))
      const response = await feeService.getDashboard()
      const data = response.data
      dispatch(setDashboard(data))

      if (data.recent_transactions) {
        setRecentTransactions(data.recent_transactions.slice(0, 5))
      }

      if (data.class_progress) {
        setClassWiseProgress(data.class_progress)
      } else {
        // Generate placeholder class-wise data from dashboard summary
        const placeholderClasses = Array.from({ length: 10 }, (_, i) => ({
          class_name: `Class ${i + 1}`,
          class_num: i + 1,
          collected: 0,
          total: 0,
          percentage: 0,
        }))
        setClassWiseProgress(placeholderClasses)
      }
    } catch (err) {
      dispatch(setError(err.response?.data?.error || 'Failed to load dashboard data'))
    }
  }

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  const formatAmount = (amount) => {
    const num = Number(amount) || 0
    return num.toLocaleString('en-IN')
  }

  const getProgressColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-500'
    if (percentage >= 60) return 'bg-blue-500'
    if (percentage >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getProgressBgColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-100'
    if (percentage >= 60) return 'bg-blue-100'
    if (percentage >= 40) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  const summaryCards = [
    {
      title: "Today's Collection",
      value: `₹${formatAmount(dashboard?.today_collection?.total_amount || 0)}`,
      subtitle: `${dashboard?.today_collection?.transaction_count || 0} transactions`,
      icon: CurrencyRupeeIcon,
      gradient: 'from-green-500 to-emerald-600',
      bgLight: 'bg-green-50',
      textColor: 'text-green-700',
    },
    {
      title: 'Year Collection',
      value: `₹${formatAmount(dashboard?.year_collection || 0)}`,
      subtitle: 'Total collected this year',
      icon: BanknotesIcon,
      gradient: 'from-blue-500 to-indigo-600',
      bgLight: 'bg-blue-50',
      textColor: 'text-blue-700',
    },
    {
      title: 'Pending Dues',
      value: dashboard?.pending_dues_count || 0,
      subtitle: 'Students with pending fees',
      icon: ExclamationTriangleIcon,
      gradient: 'from-amber-500 to-red-500',
      bgLight: 'bg-amber-50',
      textColor: 'text-amber-700',
    },
    {
      title: 'Total Students',
      value: dashboard?.total_students || 0,
      subtitle: 'Enrolled students',
      icon: UserGroupIcon,
      gradient: 'from-purple-500 to-violet-600',
      bgLight: 'bg-purple-50',
      textColor: 'text-purple-700',
    },
  ]

  const quickActions = [
    {
      title: 'Fee Collection',
      description: 'Collect fees from students',
      icon: CurrencyRupeeIcon,
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-600',
      path: '/fees',
    },
    {
      title: "Today's Report",
      description: "View today's collection details",
      icon: ClipboardDocumentListIcon,
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
      path: '/fee-reports?tab=today',
    },
    {
      title: 'Defaulters',
      description: 'Students with overdue fees',
      icon: ExclamationTriangleIcon,
      color: 'bg-amber-500',
      hoverColor: 'hover:bg-amber-600',
      path: '/fee-reports?tab=defaulters',
    },
    {
      title: 'Reports',
      description: 'Detailed fee analytics',
      icon: ChartBarIcon,
      color: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-600',
      path: '/fee-reports',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Accountant Dashboard</h1>
              <p className="text-sm text-gray-600">Fee Management System</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800">
                  Welcome, {user?.username || 'Accountant'}
                </p>
                <p className="text-xs text-gray-500">Accountant</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors shadow-md"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {summaryCards.map((card, index) => {
            const Icon = card.icon
            return (
              <div
                key={index}
                className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300"
              >
                <div className={`bg-gradient-to-r ${card.gradient} p-4`}>
                  <div className="flex items-center justify-between">
                    <div className="bg-white bg-opacity-20 p-2 rounded-lg">
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <ArrowTrendingUpIcon className="w-5 h-5 text-white opacity-70" />
                  </div>
                </div>
                <div className="p-4">
                  <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-800">{card.value}</p>
                  <p className="text-xs text-gray-400 mt-1">{card.subtitle}</p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quickActions.map((action, index) => {
              const Icon = action.icon
              return (
                <Link
                  key={index}
                  to={action.path}
                  className={`${action.color} ${action.hoverColor} text-white rounded-xl shadow-lg p-6 transition-all duration-300 hover:scale-105 hover:shadow-xl block`}
                >
                  <div className="flex flex-col items-start space-y-4">
                    <div className="bg-white bg-opacity-20 p-3 rounded-lg">
                      <Icon className="w-8 h-8" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold mb-1">{action.title}</h3>
                      <p className="text-sm opacity-90">{action.description}</p>
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>

        {/* Class-wise Collection Progress */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            <ChartBarIcon className="w-6 h-6 mr-2 text-blue-600" />
            Class-wise Collection Progress
          </h2>
          {loading && classWiseProgress.length === 0 ? (
            <div className="text-center py-8 text-gray-500">Loading class data...</div>
          ) : (
            <div className="space-y-4">
              {classWiseProgress.map((cls, index) => {
                const percentage = Math.round(cls.percentage || 0)
                return (
                  <div key={index} className="flex items-center space-x-4">
                    <div className="w-24 text-sm font-medium text-gray-700 shrink-0">
                      {cls.class_name || `Class ${cls.class_num}`}
                    </div>
                    <div className={`flex-1 h-6 rounded-full ${getProgressBgColor(percentage)} overflow-hidden`}>
                      <div
                        className={`h-full rounded-full ${getProgressColor(percentage)} transition-all duration-500 flex items-center justify-end pr-2`}
                        style={{ width: `${Math.max(percentage, 2)}%` }}
                      >
                        {percentage >= 15 && (
                          <span className="text-xs font-semibold text-white">{percentage}%</span>
                        )}
                      </div>
                    </div>
                    {percentage < 15 && (
                      <span className="text-xs font-semibold text-gray-600 w-10">{percentage}%</span>
                    )}
                    <div className="w-36 text-right text-sm text-gray-500 shrink-0">
                      ₹{formatAmount(cls.collected)} / ₹{formatAmount(cls.total)}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            <ClockIcon className="w-6 h-6 mr-2 text-purple-600" />
            Recent Transactions
          </h2>
          {loading && recentTransactions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">Loading transactions...</div>
          ) : recentTransactions.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <DocumentTextIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No recent transactions found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="pb-3 text-sm font-semibold text-gray-600">Receipt #</th>
                    <th className="pb-3 text-sm font-semibold text-gray-600">Student Name</th>
                    <th className="pb-3 text-sm font-semibold text-gray-600">Class</th>
                    <th className="pb-3 text-sm font-semibold text-gray-600 text-right">Amount</th>
                    <th className="pb-3 text-sm font-semibold text-gray-600">Method</th>
                    <th className="pb-3 text-sm font-semibold text-gray-600 text-right">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTransactions.map((txn, index) => (
                    <tr
                      key={txn.id || index}
                      className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 text-sm font-medium text-blue-600">
                        {txn.receipt_number || txn.receipt_no || '-'}
                      </td>
                      <td className="py-3 text-sm text-gray-800">
                        {txn.student_name || '-'}
                      </td>
                      <td className="py-3 text-sm text-gray-600">
                        {txn.class_name || txn.class_section || '-'}
                      </td>
                      <td className="py-3 text-sm font-semibold text-gray-800 text-right">
                        ₹{formatAmount(txn.amount_paid || txn.amount)}
                      </td>
                      <td className="py-3">
                        <span
                          className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                            txn.payment_method === 'CASH'
                              ? 'bg-green-100 text-green-700'
                              : txn.payment_method === 'UPI'
                              ? 'bg-purple-100 text-purple-700'
                              : txn.payment_method === 'CARD'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {txn.payment_method || '-'}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-500 text-right">
                        {txn.payment_date || txn.time || txn.created_at
                          ? new Date(txn.payment_date || txn.time || txn.created_at).toLocaleTimeString('en-IN', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {recentTransactions.length > 0 && (
            <div className="mt-4 text-center">
              <Link
                to="/fee-reports?tab=today"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                View All Transactions →
              </Link>
            </div>
          )}
        </div>

        {/* Floating Voice Button & Confirmation Dialog */}
        <FloatingVoiceButton />
        <ConfirmationDialog />
        <VoiceReceiptModal />
      </div>
    </div>
  )
}

export default AccountantDashboardPage
